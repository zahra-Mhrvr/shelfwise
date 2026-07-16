from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from library.models import Book, Loan, Member


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client():
    user = User.objects.create_user(username="librarian", password="password")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


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
def test_create_book(auth_client):
    response = auth_client.post(
        "/api/books/",
        {
            "title": "Django In Practice",
            "author": "Dana Web",
            "total_copies": 3,
            "available_copies": 3,
        },
        format="json",
    )

    assert response.status_code == 201
    assert Book.objects.count() == 1
    assert response.data["title"] == "Django In Practice"
    assert response.data["available_copies"] == 3


@pytest.mark.django_db
def test_book_endpoint_lists_books(api_client, book):
    response = api_client.get("/api/books/")

    assert response.status_code == 200
    assert response.data["results"][0]["title"] == book.title


@pytest.mark.django_db
def test_book_endpoint_searches_and_orders_books(api_client, book):
    Book.objects.create(
        title="Python Patterns",
        author="Pat Developer",
        total_copies=2,
        available_copies=2,
    )

    response = api_client.get("/api/books/?search=python&ordering=-title")

    assert response.status_code == 200
    assert response.data["results"][0]["title"] == "Python Patterns"


@pytest.mark.django_db
def test_anonymous_user_cannot_create_book(api_client):
    response = api_client.post(
        "/api/books/",
        {
            "title": "Django In Practice",
            "author": "Dana Web",
            "total_copies": 3,
            "available_copies": 3,
        },
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_member_endpoint_creates_member(auth_client):
    response = auth_client.post(
        "/api/members/",
        {"name": "Grace Hopper", "email": "grace@example.com"},
        format="json",
    )

    assert response.status_code == 201
    assert Member.objects.filter(email="grace@example.com").exists()


@pytest.mark.django_db
def test_borrow_endpoint_creates_loan_and_decreases_available_copies(
    auth_client,
    book,
    member,
):
    response = auth_client.post(
        "/api/loans/borrow/",
        {"book": book.id, "member": member.id},
        format="json",
    )

    book.refresh_from_db()

    assert response.status_code == 201
    assert response.data["book"] == book.id
    assert response.data["member"] == member.id
    assert book.available_copies == 0
    assert Loan.objects.count() == 1


@pytest.mark.django_db
def test_borrow_endpoint_rejects_unavailable_book(auth_client, book, member):
    book.borrow_copy()
    book.save(update_fields=["available_copies"])

    response = auth_client.post(
        "/api/loans/borrow/",
        {"book": book.id, "member": member.id},
        format="json",
    )

    assert response.status_code == 409
    assert response.data["detail"] == "no available copies"
    assert Loan.objects.count() == 0


@pytest.mark.django_db
def test_borrow_endpoint_rejects_missing_request_data(auth_client):
    response = auth_client.post(
        "/api/loans/borrow/",
        {"book": 1},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["detail"] == "book and member are required"


@pytest.mark.django_db
def test_borrow_endpoint_returns_not_found_for_missing_book(auth_client, member):
    response = auth_client.post(
        "/api/loans/borrow/",
        {"book": 999, "member": member.id},
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_return_book_endpoint_marks_loan_returned_and_restores_available_copy(
    auth_client,
    book,
    member,
):
    book.borrow_copy()
    book.save(update_fields=["available_copies"])
    loan = Loan.objects.create(
        book=book,
        member=member,
        due_on=timezone.localdate() + timedelta(days=14),
    )

    response = auth_client.post(f"/api/loans/{loan.id}/return_book/")

    book.refresh_from_db()
    loan.refresh_from_db()

    assert response.status_code == 200
    assert response.data["id"] == loan.id
    assert response.data["returned_on"] == str(timezone.localdate())
    assert loan.returned_on == timezone.localdate()
    assert book.available_copies == 1


@pytest.mark.django_db
def test_return_book_endpoint_rejects_already_returned_loan(auth_client, book, member):
    book.borrow_copy()
    book.save(update_fields=["available_copies"])
    loan = Loan.objects.create(
        book=book,
        member=member,
        due_on=timezone.localdate() + timedelta(days=14),
        returned_on=timezone.localdate(),
    )

    response = auth_client.post(f"/api/loans/{loan.id}/return_book/")

    assert response.status_code == 409
    assert response.data["detail"] == "loan has already been returned"


@pytest.mark.django_db
def test_active_loans_endpoint_lists_only_active_loans(api_client, book, member):
    active_loan = Loan.objects.create(
        book=book,
        member=member,
        due_on=timezone.localdate() + timedelta(days=14),
    )
    returned_loan = Loan.objects.create(
        book=book,
        member=member,
        due_on=timezone.localdate() + timedelta(days=14),
        returned_on=timezone.localdate(),
    )

    response = api_client.get("/api/loans/active/")

    returned_ids = {loan["id"] for loan in response.data["results"]}

    assert response.status_code == 200
    assert active_loan.id in returned_ids
    assert returned_loan.id not in returned_ids


@pytest.mark.django_db
def test_loans_endpoint_filters_active_loans(api_client, book, member):
    active_loan = Loan.objects.create(
        book=book,
        member=member,
        due_on=timezone.localdate() + timedelta(days=14),
    )
    returned_loan = Loan.objects.create(
        book=book,
        member=member,
        due_on=timezone.localdate() + timedelta(days=14),
        returned_on=timezone.localdate(),
    )

    response = api_client.get("/api/loans/?active=true")

    returned_ids = {loan["id"] for loan in response.data["results"]}

    assert response.status_code == 200
    assert active_loan.id in returned_ids
    assert returned_loan.id not in returned_ids


@pytest.mark.django_db
def test_overdue_loans_endpoint_lists_only_active_overdue_loans(
    api_client,
    book,
    member,
    caplog,
):
    overdue_loan = Loan.objects.create(
        book=book,
        member=member,
        due_on=timezone.localdate() - timedelta(days=1),
    )
    Loan.objects.create(
        book=book,
        member=member,
        due_on=timezone.localdate() + timedelta(days=14),
    )
    Loan.objects.create(
        book=book,
        member=member,
        due_on=timezone.localdate() - timedelta(days=7),
        returned_on=timezone.localdate(),
    )

    with caplog.at_level("INFO", logger="library.views"):
        response = api_client.get("/api/loans/overdue/")

    assert response.status_code == 200
    assert response.data["results"] == [
        {
            "id": overdue_loan.id,
            "book_title": book.title,
            "member_email": member.email,
            "borrowed_on": str(overdue_loan.borrowed_on),
            "due_on": str(overdue_loan.due_on),
        }
    ]
    assert "Overdue loans report generated" in caplog.messages
