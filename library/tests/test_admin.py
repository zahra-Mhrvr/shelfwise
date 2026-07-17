from datetime import timedelta

import pytest
from django.contrib.admin.sites import AdminSite
from django.utils import timezone

from library.admin import LoanAdmin
from library.models import Book, Loan, Member


@pytest.fixture
def loan_admin():
    return LoanAdmin(Loan, AdminSite())


@pytest.fixture
def book():
    return Book.objects.create(
        title="Clean Code",
        author="Robert C. Martin",
        total_copies=1,
        available_copies=1,
    )


@pytest.fixture
def member():
    return Member.objects.create(name="Ada Lovelace", email="ada@example.com")


@pytest.mark.django_db
def test_loan_admin_decreases_available_copies_when_creating_active_loan(
    loan_admin,
    book,
    member,
):
    loan = Loan(
        book=book,
        member=member,
        due_on=timezone.localdate() + timedelta(days=14),
    )

    loan_admin.save_model(request=None, obj=loan, form=None, change=False)

    book.refresh_from_db()

    assert book.available_copies == 0


@pytest.mark.django_db
def test_loan_admin_restores_available_copy_when_marking_loan_returned(
    loan_admin,
    book,
    member,
):
    book.available_copies = 0
    book.save(update_fields=["available_copies"])
    loan = Loan.objects.create(
        book=book,
        member=member,
        due_on=timezone.localdate() + timedelta(days=14),
    )

    loan.returned_on = timezone.localdate()
    loan_admin.save_model(request=None, obj=loan, form=None, change=True)

    book.refresh_from_db()

    assert book.available_copies == 1
