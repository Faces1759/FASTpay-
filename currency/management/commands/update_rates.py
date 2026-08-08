import requests
from django.core.management.base import BaseCommand
from currency.models import Currency, ExchangeRate


class Command(BaseCommand):
    help = "Fetch live exchange rates and update the database"

    def handle(self, *args, **options):
        try:
            response = requests.get(
                "https://api.exchangerate-api.com/v4/latest/NGN",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            rates = data.get("rates", {})
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to fetch live rates: {e}"))
            self.stdout.write(self.style.WARNING("Keeping existing fixed/manual rates."))
            return

        updated_count = 0

        for currency in Currency.objects.filter(is_active=True):
            code = currency.code
            if code in rates and rates[code] > 0:
                # API gives NGN -> foreign, we need foreign -> NGN (invert)
                rate_to_ngn = 1 / rates[code]

                exchange_rate, _ = ExchangeRate.objects.get_or_create(currency=currency)

                # Don't overwrite manual overrides
                if exchange_rate.source == 'manual':
                    self.stdout.write(
                        self.style.WARNING(f"Skipped {code} (manual override in place)")
                    )
                    continue

                exchange_rate.rate_to_ngn = round(rate_to_ngn, 4)
                exchange_rate.source = 'live'
                exchange_rate.save()

                self.stdout.write(
                    self.style.SUCCESS(f"Updated {code}: ₦{exchange_rate.rate_to_ngn}")
                )
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f"No live rate found for {code}, keeping existing rate.")
                )

        self.stdout.write(self.style.SUCCESS(f"Done. {updated_count} rates updated."))