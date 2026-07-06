import pytest

from library.domain import Book, EmailAddress, Loan, Member


def test_book_can_be_borrowed():
    book = Book(title="Clean Code", author="Robert C. Martin", total_copies=1)

    book.borrow_copy()

    assert book.available_copies == 0


def test_book_cannot_be_borrowed_when_no_copies_available():
    book = Book(title="Clean Code", author="Robert C. Martin", total_copies=1)
    book.borrow_copy()

    with pytest.raises(ValueError, match="no available copies"):
        book.borrow_copy()


def test_book_can_be_returned():
    book = Book(title="Clean Code", author="Robert C. Martin", total_copies=1)
    book.borrow_copy()

    book.return_copy()

    assert book.available_copies == 1


def test_book_cannot_be_created_without_copies():
    with pytest.raises(ValueError, match="a book must have at least one copy"):
        Book(title="Clean Code", author="Robert C. Martin", total_copies=0)


def test_book_cannot_return_more_copies_than_it_owns():
    book = Book(title="Clean Code", author="Robert C. Martin", total_copies=1)

    with pytest.raises(ValueError, match="all copies are already available"):
        book.return_copy()


def test_member_has_name_and_email():
    email = EmailAddress("reader@example.com")

    member = Member(name="Ada Lovelace", email=email)

    assert member.name == "Ada Lovelace"
    assert member.email == email


def test_email_address_must_contain_at_symbol():
    with pytest.raises(ValueError, match="email address must contain @"):
        EmailAddress("reader.example.com")



def test_loan_can_be_marked_returned():
    loan = Loan(book_id=1, member_id=1)

    loan.mark_returned()

    assert loan.returned_on is not None


def test_loan_cannot_be_returned_twice():
    loan = Loan(book_id=1, member_id=1)
    loan.mark_returned()

    with pytest.raises(ValueError, match="loan has already been returned"):
        loan.mark_returned()


def test_returned_loan_is_not_overdue():
    loan = Loan(book_id=1, member_id=1)
    loan.due_on = loan.borrowed_on
    loan.mark_returned()

    assert loan.is_overdue() is False
