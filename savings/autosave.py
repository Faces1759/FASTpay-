from decimal import Decimal
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from wallet.models import Wallet
from .models import SavingsPlan, SavingsDeposit


def run_autosave():
    today = timezone.now().date()

    plans = SavingsPlan.objects.filter(
        auto_save=True,
        status="active"
    )

    for plan in plans:

        if plan.next_auto_save and plan.next_auto_save <= today:

            wallet = Wallet.objects.get(user=plan.user)

            amount = Decimal(str(plan.amount_per_deposit))

            if wallet.balance >= amount:

                wallet.balance -= amount
                wallet.save()

                plan.current_balance += amount

                SavingsDeposit.objects.create(
                    plan=plan,
                    amount=amount
                )

                plan.last_auto_save = today

                if plan.frequency == "daily":
                    plan.next_auto_save += timedelta(days=1)

                elif plan.frequency == "weekly":
                    plan.next_auto_save += timedelta(weeks=1)

                elif plan.frequency == "monthly":
                    plan.next_auto_save += relativedelta(months=1)

                elif plan.frequency == "yearly":
                    plan.next_auto_save += relativedelta(years=1)

                if plan.current_balance >= plan.target_amount:
                    plan.status = "completed"

                plan.save()