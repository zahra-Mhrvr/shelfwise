from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID, uuid4


@dataclass(frozen=True)
class EmailAddress:
    value: str

    def __post_init__(self) -> None:
        if "@" not in self.value:
            raise ValueError("email address must contain @")


class Book:
    def __init__(self, title: str, author: str, total_copies: int) -> None:
        if total_copies < 1:
            raise ValueError("a book must have at least one copy")
        self.id = uuid4()
        self.title = title
        self.author = author
        self.total_copies = total_copies
        self.available_copies = total_copies

    def __eq__(self, other) -> bool:
        if not isinstance(other, Book):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def borrow_copy(self) -> None:
        if self.available_copies == 0:
            raise ValueError("no available copies")
        self.available_copies -= 1

    def return_copy(self) -> None:
        if self.available_copies == self.total_copies:
            raise ValueError("all copies are already available")
        self.available_copies += 1


class Member:
    def __init__(self, name: str, email: EmailAddress) -> None:
        self.id = uuid4()
        self.name = name
        self.email = email


class Loan:
    def __init__(self, book_id: UUID, member_id: UUID) -> None:
        self.id = uuid4()
        self.book_id = book_id
        self.member_id = member_id
        self.borrowed_on = date.today()
        self.due_on = self.borrowed_on + timedelta(days=14)
        self.returned_on: date | None = None

    def mark_returned(self) -> None:
        if self.returned_on is not None:
            raise ValueError("loan has already been returned")
        self.returned_on = date.today()

    def is_overdue(self) -> bool:
        if self.returned_on is not None:
            return False
        return date.today() > self.due_on
