from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Book, Loan, Member
from .serializers import BookSerializer, LoanSerializer, MemberSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().order_by("title")
    serializer_class = BookSerializer


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all().order_by("name")
    serializer_class = MemberSerializer


class LoanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Loan.objects.select_related("book", "member").all().order_by("-borrowed_on")
    serializer_class = LoanSerializer

    @action(detail=False, methods=["post"])
    def borrow(self, request):
        book_id = request.data.get("book")
        member_id = request.data.get("member")

        if book_id is None or member_id is None:
            return Response(
                {"detail": "book and member are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            book = get_object_or_404(Book.objects.select_for_update(), pk=book_id)
            member = get_object_or_404(Member, pk=member_id)

            try:
                book.borrow_copy()
            except ValueError as exc:
                return Response(
                    {"detail": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            book.save(update_fields=["available_copies"])
            loan = Loan.objects.create(
                book=book,
                member=member,
                due_on=timezone.localdate() + timedelta(days=14),
            )

        return Response(LoanSerializer(loan).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def return_book(self, request, pk=None):
        loan = self.get_object()

        with transaction.atomic():
            try:
                loan.mark_returned()
                loan.book.return_copy()
            except ValueError as exc:
                return Response(
                    {"detail": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            loan.save(update_fields=["returned_on"])
            loan.book.save(update_fields=["available_copies"])

        return Response(LoanSerializer(loan).data)

    @action(detail=False, methods=["get"])
    def active(self, request):
        loans = self.get_queryset().filter(returned_on__isnull=True)
        serializer = self.get_serializer(loans, many=True)
        return Response(serializer.data)
