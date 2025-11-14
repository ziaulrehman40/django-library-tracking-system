from celery import shared_task
from .models import Loan
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

@shared_task
def send_loan_notification(loan_id):
    try:
        loan = Loan.objects.get(id=loan_id)
        member_email = loan.member.user.email
        book_title = loan.book.title
        send_mail(
            subject='Book Loaned Successfully',
            message=f'Hello {loan.member.user.username},\n\nYou have successfully loaned "{book_title}".\nPlease return it by the due date.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member_email],
            fail_silently=False,
        )
    except Loan.DoesNotExist:
        pass

@shared_task
def check_overdue_loans():
    # Query all loans where is_returned is False and due_date is past.
    # Send an email reminder to each member with overdue books.
    today = timezone.now().date()
    overdue_loans = Loan.objects.select_related('book','member__user').filter(
        is_returned=False,
        due_date__lt=today
    )

    # TODO: Use batch query
    for loan in overdue_loans:
        if not loan.member.user.email:
           continue

        send_mail(
            subject='Overdue Book Reminder',
            message=f'Hello {loan.member.user.username},\n'
                  f'Your Book "{loan.book.title}" is overdue (due date: {loan.due_date}).\n'
                  f'Please return as soon as possible.\n\n'
                  f'Thanks!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[loan.member.user.email],
            fail_silently=False,
        )


# Add Overdue Loan Notification
# 📌 Description:
# Implement a Celery task that runs daily to check for overdue book loans and sends email notifications to members.
# 📍 Requirements:
# Update the Loan Model:
# Add a due_date field with a default value set to 14 days from the loan_date. x
# Create a Celery Periodic Task:
# Define a task named check_overdue_loans that executes daily.x
# The task should:
# Query all loans where is_returned is False and due_date is past.x
# Send an email reminder to each member with overdue books.x
# Apply Migrations:x
# Make and apply the necessary database migrations to accommodate the updated model.x
# Verify Task Execution:
# Test the Celery task to ensure it correctly identifies overdue loans and sends notifications.


# Configure Celery Beat Scheduler (optional):
# Only take on this task if you are familiar with Celery Beat, this task can be time consuming.
# Ensure that the check_overdue_loans task is scheduled to run daily using Celery Beat.
# Update docker-compose.yml:
# Add a celery-beat service to handle the periodic tasks.
