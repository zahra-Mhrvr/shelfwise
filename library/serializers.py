from rest_framework import serializers

from .models import Book, Loan, Member


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["id", "title", "author", "total_copies", "available_copies"]


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ["id", "name", "email"]


class LoanSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True)
    member_email = serializers.EmailField(source="member.email", read_only=True)

    class Meta:
        model = Loan
        fields = [
            "id",
            "book",
            "book_title",
            "member",
            "member_email",
            "borrowed_on",
            "due_on",
            "returned_on",
        ]
