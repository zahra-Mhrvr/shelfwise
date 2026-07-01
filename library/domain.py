from datetime import date, timedelta


class Book:
    def __init__(self, title: str, author: str, copies: int) -> None:
        if copies < 0:
            raise ValueError("copies cannot be negative")
        self.title = title
        self.author = author
        self.copies = copies

    def borrow_copy(self) -> None:
        if self.copies == 0:
            raise ValueError(f"{self.title} is not available")
        self.copies -= 1

    def return_copy(self) -> None:
        self.copies += 1


class Member:
    def __init__(self, name: str, email: str) -> None:
        self.name = name
        self.email = email


class Loan:
    def __init__(self, book: Book, member: Member) -> None:
        self.book = book
        self.member = member
        self.borrowed_on = date.today()
        self.due_on = self.borrowed_on + timedelta(days=14)
        self.returned_on = None

    def mark_returned(self) -> None:
        self.returned_on = date.today()
        self.book.return_copy()

    def is_overdue(self) -> bool:
        if self.returned_on is not None:
            return False
        return date.today() > self.due_on
