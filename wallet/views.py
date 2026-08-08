from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from notifications.utils import create_notification

from .models import Wallet, Transaction, Beneficiary, Savings
from .serializers import WalletSerializer
from .banks import BANKS

import qrcode
from io import BytesIO
from django.http import HttpResponse

User = get_user_model()


class DepositView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount")

        if amount is None:
            return Response(
                {"error": "Amount is required"},
                status=400
            )

        try:
            amount = Decimal(str(amount))
        except:
            return Response(
                {"error": "Invalid amount format"},
                status=400
            )

        if amount <= 0:
            return Response(
                {"error": "Amount must be greater than 0"},
                status=400
            )

        wallet, _ = Wallet.objects.get_or_create(
            user=request.user
        )

        wallet.balance += amount
        wallet.save()
        
       # send_mail(
#     subject="FASTpay Deposit Alert",
#     message=f"""
# Hello {request.user.username},
#
# Your wallet has been credited.
#
# Amount: ₦{amount}
#
# Available Balance: ₦{wallet.balance}
#
# Thank you for using FASTpay.
# """,
#     from_email=settings.DEFAULT_FROM_EMAIL,
#     recipient_list=[request.user.email],
#     fail_silently=False,
# )

        Transaction.objects.create(
            user=request.user,
            amount=amount,
            transaction_type="deposit"
        )
        
        create_notification(
             user=request.user,
               title="Deposit Successful",
                   message=f"₦{amount} has been credited to your FASTpay wallet."
        )

        return Response({
            "message": "Deposit successful",
            "balance": str(wallet.balance)
        })


class WithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount")

        if amount is None:
            return Response(
                {"error": "Amount is required"},
                status=400
            )

        try:
            amount = Decimal(str(amount))
        except:
            return Response(
                {"error": "Invalid amount format"},
                status=400
            )

        if amount <= 0:
            return Response(
                {"error": "Amount must be greater than 0"},
                status=400
            )

        wallet, _ = Wallet.objects.get_or_create(
            user=request.user
        )

        if wallet.balance < amount:
            return Response(
                {"error": "Insufficient balance"},
                status=400
            )

        wallet.balance -= amount
        wallet.save()
        
      # send_mail(
#     subject="FASTpay Withdrawal Alert",
#     message=f"""
# Hello {request.user.username},
#
# Your FASTpay wallet has been debited successfully.
#
# Amount: ₦{amount}
#
# Available Balance: ₦{wallet.balance}
#
# Transaction Type: Withdrawal
#
# Thank you for using FASTpay.
# """,
#     from_email=settings.DEFAULT_FROM_EMAIL,
#     recipient_list=[request.user.email],
#     fail_silently=True,
# )

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

        return Response({
            "balance": wallet.balance
        })


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
            return Response(
                {"error": "account_number and amount are required"},
                status=400
            )

        try:
            amount = Decimal(str(amount))
        except:
            return Response(
                {"error": "Invalid amount format"},
                status=400
            )

        if amount <= 0:
            return Response(
                {"error": "Amount must be greater than 0"},
                status=400
            )

        try:
            recipient_wallet = Wallet.objects.get(
                account_number=account_number
            )
            recipient = recipient_wallet.user

        except Wallet.DoesNotExist:
            return Response(
                {"error": "Account number not found"},
                status=404
            )

        if recipient == request.user:
            return Response(
                {"error": "You cannot transfer to yourself"},
                status=400
            )

        sender_wallet = Wallet.objects.get(user=request.user)

        if not sender_wallet.pin:
            return Response(
                {"error": "Please set your transaction PIN first"},
                status=400
            )

        if sender_wallet.pin != pin:
            return Response(
                {"error": "Invalid transaction PIN"},
                status=400
            )

        if sender_wallet.balance < amount:
            return Response(
                {"error": "Insufficient balance"},
                status=400
            )

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
        return Response({
            "banks": BANKS
        })
        
class AccountDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(
            user=request.user
        )

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
            return Response(
                {"error": "PIN is required"},
                status=400
            )

        if len(pin) != 4 or not pin.isdigit():
            return Response(
                {"error": "PIN must be exactly 4 digits"},
                status=400
            )

        wallet, _ = Wallet.objects.get_or_create(
            user=request.user
        )

        wallet.pin = pin
        wallet.save()

        return Response({
            "message": "Transaction PIN set successfully"
        })
        
class AddBeneficiaryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        nickname = request.data.get("nickname")
        account_number = request.data.get("account_number")

        if not nickname or not account_number:
            return Response(
                {"error": "nickname and account_number are required"},
                status=400
            )

        try:
            Wallet.objects.get(account_number=account_number)
        except Wallet.DoesNotExist:
            return Response(
                {"error": "Account number not found"},
                status=404
            )

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
        
class AddBeneficiaryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        nickname = request.data.get("nickname")
        account_number = request.data.get("account_number")

        if not nickname or not account_number:
            return Response(
                {"error": "nickname and account_number are required"},
                status=400
            )

        try:
            Wallet.objects.get(account_number=account_number)
        except Wallet.DoesNotExist:
            return Response(
                {"error": "Account number not found"},
                status=404
            )

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
            return Response(
                {"error": "Beneficiary ID is required"},
                status=400
            )

        try:
            beneficiary = Beneficiary.objects.get(
                id=beneficiary_id,
                user=request.user
            )
        except Beneficiary.DoesNotExist:
            return Response(
                {"error": "Beneficiary not found"},
                status=404
            )

        beneficiary.delete()

        return Response({
            "message": "Beneficiary deleted successfully"
        })
        
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

        return HttpResponse(
            buffer.getvalue(),
            content_type="image/png"
        )
        
class UpdatePhoneNumberView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        phone_number = request.data.get("phone_number")

        if not phone_number:
            return Response(
                {"error": "Phone number is required"},
                status=400
            )

        wallet, _ = Wallet.objects.get_or_create(
            user=request.user
        )

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
            return Response(
                {"error": "Amount, plan and duration are required"},
                status=400
            )

        try:
            amount = Decimal(str(amount))
        except:
            return Response(
                {"error": "Invalid amount"},
                status=400
            )

        wallet = Wallet.objects.get(user=request.user)

        if wallet.balance < amount:
            return Response(
                {"error": "Insufficient balance"},
                status=400
            )

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

        return Response({
            "balance": str(total)
        })


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