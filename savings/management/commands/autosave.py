from django.core.management.base import BaseCommand
from savings.autosave import run_autosave


class Command(BaseCommand):
    help = "Run FASTpay AutoSave"

    def handle(self, *args, **options):
        run_autosave()
        self.stdout.write(
            self.style.SUCCESS(
                "FASTpay AutoSave completed successfully."
            )
        )