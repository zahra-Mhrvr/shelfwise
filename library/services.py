import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from library.domain import Loan
from library.exceptions import (
    BookNotFound,
    BookReturnRejected,
    BookUnavailable,
    LoanAlreadyReturned,
    LoanNotFound,
    MemberNotFound,
)
from library.models import Loan as LoanModel

logger = logging.getLogger(__name__)


class InMemoryBookRepository:
    def __init__(self) -> None:
        self._books = {}

    def add(self, book) -> None:
        self._books[book.id] = book

    def get(self, book_id):
        try:
            return self._books[book_id]
        except KeyError as exc:
            raise BookNotFound(f"book {book_id} was not found") from exc



class InMemoryMemberRepository:
    def __init__(self) -> None:
        self._members = {}

    def add(self, member) -> None:
        self._members[member.id] = member

    def get(self, member_id):
        try:
            return self._members[member_id]
        except KeyError as exc:
            raise MemberNotFound(f"member {member_id} was not found") from exc


class InMemoryLoanRepository:
    def __init__(self) -> None:
        self._loans = {}
        self._next_id = 1

    def add(self, loan) -> int:
        loan_id = self._next_id
        self._loans[loan_id] = loan
        self._next_id += 1
        return loan_id

    def get(self, loan_id):
        try:
            return self._loans[loan_id]
        except KeyError as exc:
            raise LoanNotFound(f"loan {loan_id} was not found") from exc


class BorrowBookService:
    def __init__(self, book_repository, member_repository, loan_repository) -> None:
        self.book_repository = book_repository
        self.member_repository = member_repository
        self.loan_repository = loan_repository

    def borrow(self, book_id, member_id):
        logger.info("Borrow request started", extra={"book_id": str(book_id), "member_id": str(member_id)})
        book = self.book_repository.get(book_id)
        member = self.member_repository.get(member_id)

        try:
            book.borrow_copy()
        except ValueError as exc:
            logger.warning("Borrow request rejected: unavailable book", extra={"book_id": str(book_id)})
            raise BookUnavailable(str(exc)) from exc

        loan = Loan(book_id=book.id, member_id=member.id)

        self.book_repository.add(book)
        self.loan_repository.add(loan)
        logger.info("Borrow request completed", extra={"loan_id": str(loan.id)})
        return loan


class ReturnBookService:
    def __init__(self, book_repository, loan_repository) -> None:
        self.book_repository = book_repository
        self.loan_repository = loan_repository

    def return_book(self, loan_id):
        logger.info("Return request started", extra={"loan_id": str(loan_id)})

        loan = self.loan_repository.get(loan_id)
        book = self.book_repository.get(loan.book_id)

        try:
            loan.mark_returned()
        except ValueError as exc:
            logger.warning(
                "Return request rejected: loan already returned",
                extra={"loan_id": str(loan_id)},
            )
            raise LoanAlreadyReturned(str(exc)) from exc

        book.return_copy()

        self.book_repository.add(book)
        self.loan_repository.add(loan)

        logger.info(
            "Return request completed",
            extra={"loan_id": str(loan_id), "book_id": str(book.id)},
        )
        return loan


class DjangoBorrowBookService:
    def borrow(self, book, member):
        logger.info(
            "Borrow request started",
            extra={"book_id": str(book.id), "member_id": str(member.id)},
        )

        try:
            with transaction.atomic():
                book.borrow_copy()
                book.save(update_fields=["available_copies"])
                loan = LoanModel.objects.create(
                    book=book,
                    member=member,
                    due_on=timezone.localdate() + timedelta(days=14),
                )
        except ValueError as exc:
            logger.warning(
                "Borrow request rejected: unavailable book",
                extra={"book_id": str(book.id)},
            )
            raise BookUnavailable(str(exc)) from exc

        logger.info("Borrow request completed", extra={"loan_id": str(loan.id)})
        return loan


class DjangoReturnBookService:
    def return_book(self, loan):
        logger.info("Return request started", extra={"loan_id": str(loan.id)})

        try:
            with transaction.atomic():
                loan.mark_returned()
                loan.book.return_copy()
                loan.save(update_fields=["returned_on"])
                loan.book.save(update_fields=["available_copies"])
        except ValueError as exc:
            message = str(exc)
            logger.warning(
                "Return request rejected",
                extra={"loan_id": str(loan.id), "reason": message},
            )
            if message == "loan has already been returned":
                raise LoanAlreadyReturned(message) from exc
            raise BookReturnRejected(message) from exc

        logger.info(
            "Return request completed",
            extra={"loan_id": str(loan.id), "book_id": str(loan.book.id)},
        )
        return loan
