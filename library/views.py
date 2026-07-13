from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .exceptions import BookReturnRejected, BookUnavailable, LoanAlreadyReturned
from .models import Book, Loan, Member
from .serializers import BookSerializer, LoanSerializer, MemberSerializer
from .services import DjangoBorrowBookService, DjangoReturnBookService


def conflict(message: str) -> Response:
    return Response({"detail": message}, status=status.HTTP_409_CONFLICT)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().order_by("title")
    serializer_class = BookSerializer


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all().order_by("name")
    serializer_class = MemberSerializer


class LoanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Loan.objects.select_related("book", "member").all().order_by("-borrowed_on")
    )
    serializer_class = LoanSerializer
    borrow_service_class = DjangoBorrowBookService
    return_service_class = DjangoReturnBookService

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
        serializer = self.get_serializer(loans, many=True)
        return Response(serializer.data)
