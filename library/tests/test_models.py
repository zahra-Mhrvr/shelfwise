from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.utils import timezone

from library.models import Book, Loan, Member


@pytest.mark.django_db
def test_book_can_be_saved_to_database():
    book = Book.objects.create(
        title="Clean Code",
        author="Robert C. Martin",
        total_copies=1,
        available_copies=1,
    )

    saved_book = Book.objects.get(id=book.id)

    assert saved_book.title == "Clean Code"
    assert str(saved_book) == "Clean Code by Robert C. Martin"


def test_book_clean_rejects_more_available_copies_than_total_copies():
    book = Book(
        title="Clean Code",
        author="Robert C. Martin",
        total_copies=1,
        available_copies=2,
    )

    with pytest.raises(ValidationError, match="available copies cannot exceed total copies"):
        book.full_clean()


@pytest.mark.django_db
def test_member_email_must_be_unique():
    Member.objects.create(name="Ada Lovelace", email="ada@example.com")
    member = Member(name="Another Ada", email="ada@example.com")

    with pytest.raises(ValidationError):
        member.full_clean()


@pytest.mark.django_db
def test_loan_connects_book_and_member():
    book = Book.objects.create(
        title="Clean Code",
        author="Robert C. Martin",
        total_copies=1,
        available_copies=0,
    )
    member = Member.objects.create(name="Ada Lovelace", email="ada@example.com")

    loan = Loan.objects.create(
        book=book,
        member=member,
        due_on=timezone.localdate() + timedelta(days=14),
    )

    assert loan.book == book
    assert loan.member == member
    assert loan.is_active is True


@pytest.mark.django_db
def test_book_with_loans_cannot_be_deleted():
    book = Book.objects.create(
        title="Clean Code",
        author="Robert C. Martin",
        total_copies=1,
        available_copies=0,
    )
    member = Member.objects.create(name="Ada Lovelace", email="ada@example.com")
    Loan.objects.create(
        book=book,
        member=member,
        due_on=timezone.localdate() + timedelta(days=14),
    )

    with pytest.raises(ProtectedError):
        book.delete()
