from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import hashlib
import hmac
import json
import requests

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from notifications.utils import create_notification

from .models import Wallet, Transaction, Beneficiary, Savings, PendingDeposit, PendingWithdrawal
from .serializers import WalletSerializer
from .banks import BANKS

import qrcode
from io import BytesIO
from django.http import HttpResponse

User = get_user_model()


class InitializeDepositView(APIView):
    """
    Starts a real deposit. Does NOT credit the wallet directly —
    it asks Paystack to create a payment session and returns the
    payment link. The wallet is only credited once Paystack confirms
    the payment via webhook (see PaystackWebhookView below).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount")
        callback_url = request.data.get("callback_url")

        if amount is None:
            return Response({"error": "Amount is required"}, status=400)

        try:
            amount = Decimal(str(amount))
        except:
            return Response({"error": "Invalid amount format"}, status=400)

        if amount <= 0:
            return Response({"error": "Amount must be greater than 0"}, status=400)

        if not request.user.email:
            return Response({"error": "Your account needs an email on file to deposit"}, status=400)

        payload = {
            "email": request.user.email,
            "amount": int(amount * 100),  # Paystack expects kobo, not naira
        }
        if callback_url:
            payload["callback_url"] = callback_url

        paystack_response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            headers={
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

        result = paystack_response.json()

        if not result.get("status"):
            return Response({"error": "Unable to start deposit. Please try again."}, status=502)

        reference = result["data"]["reference"]

        PendingDeposit.objects.create(
            user=request.user,
            reference=reference,
            amount=amount,
        )

        return Response({
            "authorization_url": result["data"]["authorization_url"],
            "reference": reference,
        })


class DepositStatusView(APIView):
    """
    Lets the frontend poll whether a specific deposit has been
    confirmed yet by the Paystack webhook.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, reference):
        try:
            pending = PendingDeposit.objects.get(reference=reference, user=request.user)
        except PendingDeposit.DoesNotExist:
            return Response({"error": "Deposit not found"}, status=404)

        return Response({
            "verified": pending.verified,
            "amount": str(pending.amount),
        })


class VerifyAccountView(APIView):
    """
    Checks a bank account number against Paystack's records and
    returns the account holder's real name, so the user can confirm
    they're sending money to the right person before withdrawing.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        account_number = request.data.get("account_number")
        bank_code = request.data.get("bank_code")

        if not account_number or not bank_code:
            return Response({"error": "account_number and bank_code are required"}, status=400)

        paystack_response = requests.get(
            "https://api.paystack.co/bank/resolve",
            headers={
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            },
            params={
                "account_number": account_number,
                "bank_code": bank_code,
            },
        )

        result = paystack_response.json()

        if not result.get("status"):
            return Response({"error": "Could not verify this account. Please check the details."}, status=400)

        return Response({
            "account_number": result["data"]["account_number"],
            "account_name": result["data"]["account_name"],
        })


class InitiateWithdrawalView(APIView):
    """
    Withdraws money OUT of FASTpay to an external bank account, via
    Paystack Transfers. The wallet balance is only HELD here (not
    deducted) — it's only permanently deducted once Paystack confirms
    the transfer succeeded (see PaystackWebhookView). If the transfer
    fails, the held funds are released back to the user automatically.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        account_number = request.data.get("account_number")
        bank_code = request.data.get("bank_code")
        account_name = request.data.get("account_name")
        amount = request.data.get("amount")
        pin = request.data.get("pin")

        if not account_number or not bank_code or not account_name:
            return Response({"error": "account_number, bank_code and account_name are required"}, status=400)

        if not pin:
            return Response({"error": "Transaction PIN is required"}, status=400)

        if amount is None:
            return Response({"error": "Amount is required"}, status=400)

        try:
            amount = Decimal(str(amount))
        except:
            return Response({"error": "Invalid amount format"}, status=400)

        if amount <= 0:
            return Response({"error": "Amount must be greater than 0"}, status=400)

        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(user=request.user)

            if not wallet.pin:
                return Response({"error": "Please set your transaction PIN first"}, status=400)

            if wallet.pin_locked_until and wallet.pin_locked_until > timezone.now():
                minutes_left = int((wallet.pin_locked_until - timezone.now()).total_seconds() / 60) + 1
                return Response(
                    {"error": f"Too many wrong PIN attempts. Try again in {minutes_left} minute(s)."},
                    status=403
                )

            if not check_password(pin, wallet.pin):
                wallet.failed_pin_attempts += 1
                if wallet.failed_pin_attempts >= 3:
                    wallet.pin_locked_until = timezone.now() + timedelta(minutes=5)
                    wallet.failed_pin_attempts = 0
                wallet.save()
                return Response({"error": "Invalid transaction PIN"}, status=400)

            wallet.failed_pin_attempts = 0
            wallet.save()

            if wallet.available_balance() < amount:
                return Response({"error": "Insufficient balance"}, status=400)

            # Create a Paystack transfer recipient for this account
            recipient_response = requests.post(
                "https://api.paystack.co/transferrecipient",
                headers={
                    "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "type": "nuban",
                    "name": account_name,
                    "account_number": account_number,
                    "bank_code": bank_code,
                    "currency": "NGN",
                },
            )
            recipient_result = recipient_response.json()

            if not recipient_result.get("status"):
                return Response({"error": "Could not set up this recipient. Please try again."}, status=502)

            recipient_code = recipient_result["data"]["recipient_code"]

            # Hold the funds now, before calling Paystack, so the user
            # can't spend the same money twice while the transfer is pending
            wallet.hold_funds(amount)

            # Initiate the actual transfer
            transfer_response = requests.post(
                "https://api.paystack.co/transfer",
                headers={
                    "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "source": "balance",
                    "amount": int(amount * 100),  # kobo
                    "recipient": recipient_code,
                    "reason": "FASTpay withdrawal",
                },
            )
            transfer_result = transfer_response.json()

            if not transfer_result.get("status"):
                # Transfer failed to even start — give the held funds back
                wallet.release_funds(amount)
                return Response({"error": "Unable to start withdrawal. Please try again."}, status=502)

            reference = transfer_result["data"]["reference"]

            PendingWithdrawal.objects.create(
                user=request.user,
                reference=reference,
                amount=amount,
                account_number=account_number,
                bank_code=bank_code,
                account_name=account_name,
            )

        return Response({
            "message": "Withdrawal initiated. You'll be notified once it's complete.",
            "reference": reference,
        })


class PaystackWebhookView(APIView):
    """
    Paystack calls this URL automatically after a payment or transfer
    completes. This is the ONLY place a wallet gets credited for a
    deposit, or permanently debited for a withdrawal. We verify the
    signature so nobody can fake this request themselves.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        signature = request.headers.get("x-paystack-signature", "")
        computed_signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode("utf-8"),
            request.body,
            hashlib.sha512,
        ).hexdigest()

        if not hmac.compare_digest(signature, computed_signature):
            return Response(status=401)

        event = json.loads(request.body)
        event_type = event.get("event")

        if event_type == "charge.success":
            reference = event["data"]["reference"]
            amount_paid = Decimal(str(event["data"]["amount"])) / 100  # back to naira

            try:
                pending = PendingDeposit.objects.get(reference=reference)
            except PendingDeposit.DoesNotExist:
                return Response(status=200)

            with transaction.atomic():
                pending = PendingDeposit.objects.select_for_update().get(reference=reference)

                if pending.verified:
                    return Response(status=200)  # already credited, don't double-credit

                if amount_paid != pending.amount:
                    return Response(status=200)  # amount mismatch, don't credit — investigate manually

                wallet, _ = Wallet.objects.select_for_update().get_or_create(user=pending.user)
                wallet.balance += pending.amount
                wallet.save()

                pending.verified = True
                pending.save()

                Transaction.objects.create(
                    user=pending.user,
                    amount=pending.amount,
                    transaction_type="deposit",
                    reference=reference,
                )

                create_notification(
                    user=pending.user,
                    title="Deposit Successful",
                    message=f"₦{pending.amount} has been credited to your FASTpay wallet.",
                )

            return Response(status=200)

        elif event_type == "transfer.success":
            reference = event["data"]["reference"]

            try:
                pending = PendingWithdrawal.objects.get(reference=reference)
            except PendingWithdrawal.DoesNotExist:
                return Response(status=200)

            with transaction.atomic():
                pending = PendingWithdrawal.objects.select_for_update().get(reference=reference)

                if pending.status == "success":
                    return Response(status=200)  # already processed

                wallet = Wallet.objects.select_for_update().get(user=pending.user)
                wallet.deduct_held_funds(pending.amount)

                pending.status = "success"
                pending.save()

                Transaction.objects.create(
                    user=pending.user,
                    amount=pending.amount,
                    transaction_type="withdraw",
                    reference=reference,
                    narration=f"Withdrawal to {pending.account_name} ({pending.account_number})",
                )

                create_notification(
                    user=pending.user,
                    title="Withdrawal Successful",
                    message=f"₦{pending.amount} has been sent to {pending.account_name}.",
                )

            return Response(status=200)

        elif event_type == "transfer.failed" or event_type == "transfer.reversed":
            reference = event["data"]["reference"]

            try:
                pending = PendingWithdrawal.objects.get(reference=reference)
            except PendingWithdrawal.DoesNotExist:
                return Response(status=200)

            with transaction.atomic():
                pending = PendingWithdrawal.objects.select_for_update().get(reference=reference)

                if pending.status in ("failed", "success"):
                    return Response(status=200)  # already processed

                wallet = Wallet.objects.select_for_update().get(user=pending.user)
                wallet.release_funds(pending.amount)

                pending.status = "failed"
                pending.save()

                create_notification(
                    user=pending.user,
                    title="Withdrawal Failed",
                    message=f"Your withdrawal of ₦{pending.amount} could not be completed. The funds have been returned to your wallet.",
                )

            return Response(status=200)

        return Response(status=200)


class WithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount")

        if amount is None:
            return Response({"error": "Amount is required"}, status=400)

        try:
            amount = Decimal(str(amount))
        except:
            return Response({"error": "Invalid amount format"}, status=400)

        if amount <= 0:
            return Response({"error": "Amount must be greater than 0"}, status=400)

        with transaction.atomic():
            wallet, _ = Wallet.objects.select_for_update().get_or_create(user=request.user)

            if wallet.balance < amount:
                return Response({"error": "Insufficient balance"}, status=400)

            wallet.balance -= amount
            wallet.save()

            Transaction.objects.create(
                user=request.user,
                amount=amount,
                transaction_type="withdraw"
            )

        create_notification(
            user=request.user,
            title="Withdrawal Successful",
            message=f"₦{amount} has been debited from your FASTpay wallet."
        )

        return Response({
            "message": "Withdrawal successful",
            "balance": str(wallet.balance)
        })


class WalletBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = Wallet.objects.get(user=request.user)
        return Response({"balance": wallet.balance})


class TransactionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = Transaction.objects.filter(
            user=request.user
        ).order_by("id")

        running_balance = Decimal("0")
        data = []

        for t in transactions:
            if t.transaction_type == "deposit":
                running_balance += t.amount
            else:
                running_balance -= t.amount

            data.append({
                "reference": t.reference,
                "type": t.transaction_type,
                "amount": str(t.amount),
                "narration": t.narration,
                "date": t.timestamp,
                "balance_after": str(running_balance)
            })

        return Response(data)


class TransferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        account_number = request.data.get("account_number")
        amount = request.data.get("amount")
        narration = request.data.get("narration", "")
        pin = request.data.get("pin")

        if not account_number or not amount:
            return Response({"error": "account_number and amount are required"}, status=400)

        if not pin:
            return Response({"error": "Transaction PIN is required"}, status=400)

        try:
            amount = Decimal(str(amount))
        except:
            return Response({"error": "Invalid amount format"}, status=400)

        if amount <= 0:
            return Response({"error": "Amount must be greater than 0"}, status=400)

        with transaction.atomic():
            # Lock both wallets in a consistent order (by id) to prevent deadlocks
            # when two transfers happen between the same two accounts at once.
            locked_wallets = list(
                Wallet.objects.select_for_update().filter(
                    Q(user=request.user) | Q(account_number=account_number)
                ).order_by("id")
            )

            sender_wallet = next((w for w in locked_wallets if w.user_id == request.user.id), None)
            recipient_wallet = next((w for w in locked_wallets if w.account_number == account_number), None)

            if not recipient_wallet:
                return Response({"error": "Account number not found"}, status=404)

            recipient = recipient_wallet.user

            if recipient == request.user:
                return Response({"error": "You cannot transfer to yourself"}, status=400)

            if not sender_wallet.pin:
                return Response({"error": "Please set your transaction PIN first"}, status=400)

            # PIN lockout check
            if sender_wallet.pin_locked_until and sender_wallet.pin_locked_until > timezone.now():
                minutes_left = int((sender_wallet.pin_locked_until - timezone.now()).total_seconds() / 60) + 1
                return Response(
                    {"error": f"Too many wrong PIN attempts. Try again in {minutes_left} minute(s)."},
                    status=403
                )

            # PIN check against the HASHED pin, not raw comparison
            if not check_password(pin, sender_wallet.pin):
                sender_wallet.failed_pin_attempts += 1
                if sender_wallet.failed_pin_attempts >= 3:
                    sender_wallet.pin_locked_until = timezone.now() + timedelta(minutes=5)
                    sender_wallet.failed_pin_attempts = 0
                sender_wallet.save()
                return Response({"error": "Invalid transaction PIN"}, status=400)

            # Correct PIN — reset the failed attempt counter
            sender_wallet.failed_pin_attempts = 0

            if sender_wallet.balance < amount:
                return Response({"error": "Insufficient balance"}, status=400)

            sender_wallet.balance -= amount
            sender_wallet.save()

            recipient_wallet.balance += amount
            recipient_wallet.save()

            Transaction.objects.create(
                user=request.user,
                amount=amount,
                transaction_type="withdraw",
                narration=narration
            )

            Transaction.objects.create(
                user=recipient,
                amount=amount,
                transaction_type="deposit",
                narration=narration
            )

        create_notification(
            user=request.user,
            title="Transfer Successful",
            message=f"You transferred ₦{amount} to {recipient.username}."
        )

        create_notification(
            user=recipient,
            title="Money Received",
            message=f"You received ₦{amount} from {request.user.username}."
        )

        return Response({
            "message": "Transfer successful",
            "recipient": recipient.username,
            "account_number": recipient_wallet.account_number,
            "amount": str(amount),
            "narration": narration,
            "balance": str(sender_wallet.balance)
        })


class BankListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"banks": BANKS})


class AccountDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        return Response({
            "username": request.user.username,
            "account_number": wallet.account_number,
            "balance": str(wallet.balance)
        })


class SetPinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pin = request.data.get("pin")

        if not pin:
            return Response({"error": "PIN is required"}, status=400)

        if len(pin) != 4 or not pin.isdigit():
            return Response({"error": "PIN must be exactly 4 digits"}, status=400)

        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        wallet.pin = make_password(pin)  # hashed, never stored raw
        wallet.failed_pin_attempts = 0
        wallet.pin_locked_until = None
        wallet.save()

        return Response({"message": "Transaction PIN set successfully"})


class AddBeneficiaryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        nickname = request.data.get("nickname")
        account_number = request.data.get("account_number")

        if not nickname or not account_number:
            return Response({"error": "nickname and account_number are required"}, status=400)

        try:
            Wallet.objects.get(account_number=account_number)
        except Wallet.DoesNotExist:
            return Response({"error": "Account number not found"}, status=404)

        beneficiary = Beneficiary.objects.create(
            user=request.user,
            nickname=nickname,
            account_number=account_number
        )

        return Response({
            "message": "Beneficiary added successfully",
            "nickname": beneficiary.nickname,
            "account_number": beneficiary.account_number
        })


class BeneficiaryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        beneficiaries = Beneficiary.objects.filter(user=request.user)
        data = []
        for beneficiary in beneficiaries:
            data.append({
                "id": beneficiary.id,
                "nickname": beneficiary.nickname,
                "account_number": beneficiary.account_number,
            })
        return Response(data)


class DeleteBeneficiaryView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        beneficiary_id = request.data.get("id")

        if not beneficiary_id:
            return Response({"error": "Beneficiary ID is required"}, status=400)

        try:
            beneficiary = Beneficiary.objects.get(id=beneficiary_id, user=request.user)
        except Beneficiary.DoesNotExist:
            return Response({"error": "Beneficiary not found"}, status=404)

        beneficiary.delete()
        return Response({"message": "Beneficiary deleted successfully"})


class QRCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = Wallet.objects.get(user=request.user)
        data = (
            f"FASTpay\n"
            f"Name: {request.user.username}\n"
            f"Account: {wallet.account_number}"
        )
        qr = qrcode.make(data)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        return HttpResponse(buffer.getvalue(), content_type="image/png")


class UpdatePhoneNumberView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        phone_number = request.data.get("phone_number")

        if not phone_number:
            return Response({"error": "Phone number is required"}, status=400)

        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        wallet.phone_number = phone_number
        wallet.save()

        return Response({
            "message": "Phone number updated successfully",
            "phone_number": wallet.phone_number
        })


class StartSavingsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount")
        plan = request.data.get("plan")
        duration = request.data.get("duration")

        if not amount or not plan or not duration:
            return Response({"error": "Amount, plan and duration are required"}, status=400)

        try:
            amount = Decimal(str(amount))
        except:
            return Response({"error": "Invalid amount"}, status=400)

        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(user=request.user)

            if wallet.balance < amount:
                return Response({"error": "Insufficient balance"}, status=400)

            wallet.balance -= amount
            wallet.save()

            savings = Savings.objects.create(
                user=request.user,
                amount=amount,
                plan=plan,
                duration=duration
            )

            Transaction.objects.create(
                user=request.user,
                amount=amount,
                transaction_type="withdraw",
                narration=f"FASTpay Akawo ({plan})"
            )

        create_notification(
            user=request.user,
            title="Savings Created",
            message=f"You saved ₦{amount} into FASTpay Akawo."
        )

        return Response({
            "message": "Savings created successfully",
            "wallet_balance": str(wallet.balance),
            "amount": str(savings.amount),
            "plan": savings.plan,
            "duration": savings.duration
        })


class SavingsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        savings = Savings.objects.filter(user=request.user)
        total = Decimal("0")
        for item in savings:
            total += item.amount
        return Response({"balance": str(total)})


class SavingsHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        savings = Savings.objects.filter(user=request.user).order_by("-id")
        data = []
        for item in savings:
            data.append({
                "id": item.id,
                "amount": str(item.amount),
                "plan": item.plan,
                "duration": item.duration,
                "date": item.created_at,
            })
        return Response(data)