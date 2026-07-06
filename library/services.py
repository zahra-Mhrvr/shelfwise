from library.domain import Loan
from library.exceptions import (
    BookNotFound,
    BookUnavailable,
    LoanAlreadyReturned,
    LoanNotFound,
    MemberNotFound,
)


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
        book = self.book_repository.get(book_id)
        member = self.member_repository.get(member_id)

        try:
            book.borrow_copy()
        except ValueError as exc:
            raise BookUnavailable(str(exc)) from exc

        loan = Loan(book_id=book.id, member_id=member.id)

        self.book_repository.add(book)
        self.loan_repository.add(loan)

        return loan


class ReturnBookService:
    def __init__(self, book_repository, loan_repository) -> None:
        self.book_repository = book_repository
        self.loan_repository = loan_repository

    def return_book(self, loan_id):
        loan = self.loan_repository.get(loan_id)
        book = self.book_repository.get(loan.book_id)
        

        try:
            loan.mark_returned()
        except ValueError as exc:
            raise LoanAlreadyReturned(str(exc)) from exc

        book.return_copy()

        self.book_repository.add(book)
        self.loan_repository.add(loan)

        return loan
