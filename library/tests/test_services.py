
import logging

import pytest

from library.domain import Book, EmailAddress, Loan, Member
from library.exceptions import (
    BookNotFound,
    BookUnavailable,
    LoanAlreadyReturned,
    LoanNotFound,
    MemberNotFound,
)
from library.services import (
    BorrowBookService,
    InMemoryBookRepository,
    InMemoryLoanRepository,
    InMemoryMemberRepository,
    ReturnBookService,
)


@pytest.fixture
def book_repository():
    return InMemoryBookRepository()


@pytest.fixture
def member_repository():
    return InMemoryMemberRepository()


@pytest.fixture
def loan_repository():
    return InMemoryLoanRepository()


@pytest.fixture
def book():
    return Book(title="Clean Code", author="Robert C. Martin", total_copies=1)


@pytest.fixture
def member():
    return Member(name="Ada Lovelace", email=EmailAddress("ada@example.com"))


@pytest.fixture
def borrow_service(book_repository, member_repository, loan_repository):
    return BorrowBookService(book_repository, member_repository, loan_repository)


@pytest.fixture
def return_service(book_repository, loan_repository):
    return ReturnBookService(book_repository, loan_repository)


def test_borrow_book_service_logs_success(
    caplog,
    book_repository,
    member_repository,
    book,
    member,
    borrow_service,
):
    book_repository.add(book)
    member_repository.add(member)

    with caplog.at_level(logging.INFO, logger="library.services"):
        loan = borrow_service.borrow(book_id=book.id, member_id=member.id)

    assert loan.book_id == book.id
    assert "Borrow request started" in caplog.messages
    assert "Borrow request completed" in caplog.messages


def test_borrow_book_service_logs_unavailable_rejection(
    caplog,
    book_repository,
    member_repository,
    book,
    member,
    borrow_service,
):
    book.borrow_copy()
    book_repository.add(book)
    member_repository.add(member)

    with caplog.at_level(logging.WARNING, logger="library.services"):
        with pytest.raises(BookUnavailable):
            borrow_service.borrow(book_id=book.id, member_id=member.id)

    assert "Borrow request rejected: unavailable book" in caplog.messages


def test_borrow_book_service_raises_book_not_found(member_repository, member, borrow_service):
    member_repository.add(member)

    with pytest.raises(BookNotFound):
        borrow_service.borrow(book_id=1, member_id=member.id)


def test_borrow_book_service_raises_member_not_found(book_repository, book, borrow_service):
    book_repository.add(book)

    with pytest.raises(MemberNotFound):
        borrow_service.borrow(book_id=book.id, member_id=1)


def test_return_book_service_logs_success(
    caplog,
    book_repository,
    loan_repository,
    book,
    return_service,
):
    book.borrow_copy()
    loan = Loan(book_id=book.id, member_id=1)
    loan_id = loan_repository.add(loan)
    book_repository.add(book)

    with caplog.at_level(logging.INFO, logger="library.services"):
        returned_loan = return_service.return_book(loan_id)

    assert returned_loan.returned_on is not None
    assert "Return request started" in caplog.messages
    assert "Return request completed" in caplog.messages


def test_return_book_service_logs_already_returned_rejection(
    caplog,
    book_repository,
    loan_repository,
    book,
    return_service,
):
    book.borrow_copy()
    loan = Loan(book_id=book.id, member_id=1)
    loan.mark_returned()
    loan_id = loan_repository.add(loan)
    book_repository.add(book)

    with caplog.at_level(logging.WARNING, logger="library.services"):
        with pytest.raises(LoanAlreadyReturned):
            return_service.return_book(loan_id)

    assert "Return request rejected: loan already returned" in caplog.messages


def test_return_book_service_raises_loan_not_found(return_service):
    with pytest.raises(LoanNotFound):
        return_service.return_book(loan_id=1)


def test_return_book_service_raises_book_not_found(loan_repository, return_service):
    loan = Loan(book_id=1, member_id=1)
    loan_id = loan_repository.add(loan)

    with pytest.raises(BookNotFound):
        return_service.return_book(loan_id)
