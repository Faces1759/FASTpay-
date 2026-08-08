from django.core.management.base import BaseCommand
from currency.models import Currency, ExchangeRate


class Command(BaseCommand):
    help = "Seed initial currencies with fixed fallback rates"

    def handle(self, *args, **options):
        currencies = [
            {"code": "USD", "name": "US Dollar", "symbol": "$", "rate": 1600.00},
            {"code": "GBP", "name": "British Pound", "symbol": "£", "rate": 2000.00},
            {"code": "EUR", "name": "Euro", "symbol": "€", "rate": 1700.00},
            {"code": "GHS", "name": "Ghanaian Cedi", "symbol": "GH₵", "rate": 105.00},
            {"code": "ZAR", "name": "South African Rand", "symbol": "R", "rate": 88.00},
            {"code": "CAD", "name": "Canadian Dollar", "symbol": "C$", "rate": 1170.00},
        ]

        for c in currencies:
            currency, created = Currency.objects.get_or_create(
                code=c["code"],
                defaults={"name": c["name"], "symbol": c["symbol"]}
            )
            ExchangeRate.objects.update_or_create(
                currency=currency,
                defaults={"rate_to_ngn": c["rate"], "source": "fixed"}
            )
            status = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{status}: {c['code']} = ₦{c['rate']}"))

        self.stdout.write(self.style.SUCCESS("Currency seeding complete."))