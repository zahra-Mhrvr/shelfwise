import pytest
from django.utils import timezone

from library.models import Book, Loan, Member


def test_book_borrow_copy_reduces_available_copies():
    book = Book(
        title="Architecture Patterns",
        author="A. Builder",
        total_copies=2,
        available_copies=2,
    )

    book.borrow_copy()

    assert book.available_copies == 1


def test_book_cannot_be_borrowed_when_unavailable():
    book = Book(
        title="Architecture Patterns",
        author="A. Builder",
        total_copies=1,
        available_copies=0,
    )

    with pytest.raises(ValueError, match="no available copies"):
        book.borrow_copy()


def test_book_return_copy_increases_available_copies():
    book = Book(
        title="Architecture Patterns",
        author="A. Builder",
        total_copies=2,
        available_copies=1,
    )

    book.return_copy()

    assert book.available_copies == 2


def test_book_cannot_return_more_copies_than_library_owns():
    book = Book(
        title="Architecture Patterns",
        author="A. Builder",
        total_copies=1,
        available_copies=1,
    )

    with pytest.raises(ValueError, match="all copies are already available"):
        book.return_copy()


def test_loan_is_active_until_it_has_return_date():
    book = Book(
        title="Testing APIs",
        author="Q. Analyst",
        total_copies=1,
        available_copies=0,
    )
    member = Member(name="Sam Reader", email="sam@example.com")
    loan = Loan(book=book, member=member, due_on=timezone.localdate())

    assert loan.is_active is True


def test_loan_mark_returned_sets_returned_on():
    book = Book(
        title="Testing APIs",
        author="Q. Analyst",
        total_copies=1,
        available_copies=0,
    )
    member = Member(name="Sam Reader", email="sam@example.com")
    loan = Loan(book=book, member=member, due_on=timezone.localdate())

    loan.mark_returned()

    assert loan.returned_on == timezone.localdate()
    assert loan.is_active is False


def test_loan_cannot_be_returned_twice():
    book = Book(
        title="Testing APIs",
        author="Q. Analyst",
        total_copies=1,
        available_copies=0,
    )
    member = Member(name="Sam Reader", email="sam@example.com")
    loan = Loan(book=book, member=member, due_on=timezone.localdate())
    loan.mark_returned()

    with pytest.raises(ValueError, match="loan has already been returned"):
        loan.mark_returned()
