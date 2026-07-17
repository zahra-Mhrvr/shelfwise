from django import forms
from django.contrib import admin
from django.db import transaction

from .models import Book, Loan, Member


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "total_copies", "available_copies"]
    search_fields = ["title", "author"]
    ordering = ["title"]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ["name", "email"]
    search_fields = ["name", "email"]
    ordering = ["name"]


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    class LoanAdminForm(forms.ModelForm):
        class Meta:
            model = Loan
            fields = "__all__"

        def clean(self):
            cleaned_data = super().clean()
            book = cleaned_data.get("book")
            returned_on = cleaned_data.get("returned_on")

            if book is None or returned_on is not None:
                return cleaned_data

            if self.instance.pk:
                previous_loan = Loan.objects.get(pk=self.instance.pk)
                is_still_same_active_book = (
                    previous_loan.returned_on is None
                    and previous_loan.book_id == book.id
                )
                if is_still_same_active_book:
                    return cleaned_data

            if book.available_copies == 0:
                raise forms.ValidationError("This book has no available copies.")

            return cleaned_data

    form = LoanAdminForm
    list_display = ["book", "member", "borrowed_on", "due_on", "returned_on"]
    list_filter = ["borrowed_on", "due_on", "returned_on"]
    search_fields = ["book__title", "member__name", "member__email"]
    ordering = ["-borrowed_on"]

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            previous_loan = None
            if change:
                previous_loan = Loan.objects.select_related("book").get(pk=obj.pk)

            self._adjust_book_availability(obj, previous_loan)
            super().save_model(request, obj, form, change)

    def _adjust_book_availability(self, loan, previous_loan):
        new_active = loan.returned_on is None

        if previous_loan is None:
            if new_active:
                self._borrow_book_copy(loan.book)
            return

        previous_active = previous_loan.returned_on is None
        book_changed = previous_loan.book_id != loan.book_id

        if previous_active and (not new_active or book_changed):
            self._return_book_copy(previous_loan.book)

        if new_active and (not previous_active or book_changed):
            self._borrow_book_copy(loan.book)

    def _borrow_book_copy(self, book):
        book.borrow_copy()
        book.save(update_fields=["available_copies"])

    def _return_book_copy(self, book):
        if book.available_copies == book.total_copies:
            return

        book.return_copy()
        book.save(update_fields=["available_copies"])
