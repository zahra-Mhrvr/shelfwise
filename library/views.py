import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .exceptions import BookReturnRejected, BookUnavailable, LoanAlreadyReturned
from .models import Book, Loan, Member
from .serializers import (
    BookSerializer,
    LoanSerializer,
    MemberSerializer,
    OverdueLoanSerializer,
)
from .services import DjangoBorrowBookService, DjangoReturnBookService

logger = logging.getLogger(__name__)


def conflict(message: str) -> Response:
    return Response({"detail": message}, status=status.HTTP_409_CONFLICT)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().order_by("title")
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ["title", "author"]
    ordering_fields = ["title", "author", "total_copies", "available_copies"]
    ordering = ["title"]


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all().order_by("name")
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ["name", "email"]
    ordering_fields = ["name", "email"]
    ordering = ["name"]


class LoanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Loan.objects.select_related("book", "member").all().order_by("-borrowed_on")
    )
    serializer_class = LoanSerializer
    borrow_service_class = DjangoBorrowBookService
    return_service_class = DjangoReturnBookService
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ["book__title", "member__email"]
    ordering_fields = ["borrowed_on", "due_on", "returned_on"]
    ordering = ["-borrowed_on"]

    def get_queryset(self):
        queryset = super().get_queryset()
        active = self.request.query_params.get("active")
        book_id = self.request.query_params.get("book")
        member_id = self.request.query_params.get("member")

        if active == "true":
            queryset = queryset.filter(returned_on__isnull=True)
        elif active == "false":
            queryset = queryset.filter(returned_on__isnull=False)

        if book_id:
            queryset = queryset.filter(book_id=book_id)

        if member_id:
            queryset = queryset.filter(member_id=member_id)

        return queryset

    @action(detail=False, methods=["post"])
    def borrow(self, request):
        book_id = request.data.get("book")
        member_id = request.data.get("member")

        if book_id is None or member_id is None:
            return Response(
                {"detail": "book and member are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        book = get_object_or_404(Book, pk=book_id)
        member = get_object_or_404(Member, pk=member_id)

        try:
            loan = self.borrow_service_class().borrow(book=book, member=member)
        except BookUnavailable as exc:
            return conflict(str(exc))

        return Response(LoanSerializer(loan).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def return_book(self, request, pk=None):
        loan = self.get_object()

        try:
            loan = self.return_service_class().return_book(loan)
        except (BookReturnRejected, LoanAlreadyReturned) as exc:
            return conflict(str(exc))

        return Response(LoanSerializer(loan).data)

    @action(detail=False, methods=["get"])
    def active(self, request):
        loans = self.get_queryset().filter(returned_on__isnull=True)
        page = self.paginate_queryset(loans)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(loans, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def overdue(self, request):
        loans = self.get_queryset().filter(
            returned_on__isnull=True,
            due_on__lt=timezone.localdate(),
        )
        logger.info("Overdue loans report generated", extra={"count": loans.count()})
        page = self.paginate_queryset(loans)
        if page is not None:
            serializer = OverdueLoanSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = OverdueLoanSerializer(loans, many=True)
        return Response(serializer.data)
