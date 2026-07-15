from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=120)
    total_copies = models.PositiveIntegerField()
    available_copies = models.PositiveIntegerField()

    def borrow_copy(self) -> None:
        if self.available_copies == 0:
            raise ValueError("no available copies")
        self.available_copies -= 1

    def return_copy(self) -> None:
        if self.available_copies == self.total_copies:
            raise ValueError("all copies are already available")
        self.available_copies += 1

    def clean(self) -> None:
        if self.available_copies > self.total_copies:
            raise ValidationError(
                {"available_copies": "available copies cannot exceed total copies"}
            )

    def __str__(self) -> str:
        return f"{self.title} by {self.author}"


class Member(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"


class Loan(models.Model):
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name="loans")
    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="loans")
    borrowed_on = models.DateField(default=timezone.localdate)
    due_on = models.DateField()
    returned_on = models.DateField(null=True, blank=True)

    def mark_returned(self) -> None:
        if self.returned_on is not None:
            raise ValueError("loan has already been returned")
        self.returned_on = timezone.localdate()

    @property
    def is_active(self) -> bool:
        return self.returned_on is None

    def is_overdue(self) -> bool:
        return self.is_active and self.due_on < timezone.localdate()
