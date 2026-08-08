import json
import gzip
from datetime import datetime
from io import StringIO, BytesIO

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.core.mail import EmailMessage
from django.conf import settings


class Command(BaseCommand):
    help = "Backup the full database to JSON and email it as a compressed attachment"

    def handle(self, *args, **options):
        self.stdout.write("Starting database backup...")

        buffer = StringIO()
        call_command(
            "dumpdata",
            exclude=["contenttypes", "auth.permission", "admin.logentry", "sessions.session"],
            indent=2,
            stdout=buffer,
        )
        json_data = buffer.getvalue()

        compressed = BytesIO()
        with gzip.GzipFile(fileobj=compressed, mode="wb") as f:
            f.write(json_data.encode("utf-8"))
        compressed.seek(0)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"fastpay_backup_{timestamp}.json.gz"

        email = EmailMessage(
            subject=f"FASTpay Database Backup - {timestamp}",
            body="Automated daily backup attached. Keep this file safe.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.EMAIL_HOST_USER],
        )
        email.attach(filename, compressed.getvalue(), "application/gzip")
        email.send()

        self.stdout.write(self.style.SUCCESS(f"Backup emailed successfully: {filename}"))