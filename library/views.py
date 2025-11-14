from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from datetime import timedelta

from .models import Author, Book, Member, Loan
from .serializers import AuthorSerializer, BookSerializer, MemberSerializer, LoanSerializer
from .tasks import send_loan_notification

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.select_related('author').all()
    serializer_class = BookSerializer
    pagination_class = PageNumberPagination

    @action(detail=True, methods=['post'])
    def loan(self, request, pk=None):
        book = self.get_object()
        if book.available_copies < 1:
            return Response({'error': 'No available copies.'}, status=status.HTTP_400_BAD_REQUEST)
        member_id = request.data.get('member_id')
        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            return Response({'error': 'Member does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        loan = Loan.objects.create(book=book, member=member)
        book.available_copies -= 1
        book.save()
        send_loan_notification.delay(loan.id)
        return Response({'status': 'Book loaned successfully.'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        book = self.get_object()
        member_id = request.data.get('member_id')
        try:
            loan = Loan.objects.get(book=book, member__id=member_id, is_returned=False)
        except Loan.DoesNotExist:
            return Response({'error': 'Active loan does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        loan.is_returned = True
        loan.return_date = timezone.now().date()
        loan.save()
        book.available_copies += 1
        book.save()
        return Response({'status': 'Book returned successfully.'}, status=status.HTTP_200_OK)

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer

    @action(detail=True, methods=['post'])
    def extend_due_date(self, request, pk=None):
        loan = self.get_object()
        additional_days = request.data.get('additional_days')

        if loan.is_returned:
            return Response(
                {'err': 'cant extend due date for returned loans'},
                status=status.HTTP_400_BAD_REQUEST
            )

        today = timezone.now().date()
        if  loan.due_date and loan.due_date < today:
            return Response(
                {'err': 'cant extend due date for overdue loan'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if additional_days is None:
            return Response(
                {'err': 'Invalid additional days provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            additional_days = int(additional_days)
            if additional_days <= 0:
                raise ValueError()
        except(ValueError, TypeError):
            return Response(
                {'err': 'additional days must be positive integer'},
                status=status.HTTP_400_BAD_REQUEST
            )

        #extend due date
        if loan.due_date:
            loan.due_date += timedelta(days=additional_days)
        else:
            loan.due_date = today + timedelta(days=additional_days)
        loan.save()

        return Response(
            LoanSerializer(loan).data,
            status=status.HTTP_200_OK
        )
