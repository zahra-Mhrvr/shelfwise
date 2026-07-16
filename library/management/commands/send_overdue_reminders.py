import logging

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from library.models import Loan

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send reminder emails for active overdue loans."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show who would be emailed without sending messages.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        overdue_loans = Loan.objects.select_related("book", "member").filter(
            returned_on__isnull=True,
            due_on__lt=timezone.localdate(),
        )

        sent_count = 0
        for loan in overdue_loans:
            subject = f"Overdue book reminder: {loan.book.title}"
            message = (
                f"Hello {loan.member.name},\n\n"
                f"'{loan.book.title}' was due on {loan.due_on}. "
                "Please return it when you can.\n"
            )

            if dry_run:
                self.stdout.write(f"Would email {loan.member.email}: {subject}")
            else:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [loan.member.email],
                    fail_silently=False,
                )
                sent_count += 1

        logger.info(
            "Overdue reminder job completed",
            extra={"dry_run": dry_run, "sent_count": sent_count},
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {overdue_loans.count()} overdue loan(s); sent {sent_count}."
            )
        )
