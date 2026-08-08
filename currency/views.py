from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction as db_transaction
from .models import Currency, ExchangeRate, CurrencyWallet, CurrencyTransaction
from .serializers import (
    CurrencySerializer,
    CurrencyWalletSerializer,
    CurrencyDepositSerializer,
    CurrencyWithdrawSerializer,
    ExchangeToForeignSerializer,
    ExchangeToNgnSerializer,
    CurrencyTransactionSerializer,
)
from wallet.models import Wallet


class CurrencyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        currencies = Currency.objects.filter(is_active=True)
        return Response(CurrencySerializer(currencies, many=True).data)


class MyCurrencyWalletsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallets = CurrencyWallet.objects.filter(user=request.user)
        return Response(CurrencyWalletSerializer(wallets, many=True).data)


class CurrencyDepositView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CurrencyDepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['currency_code'].upper()
        amount = serializer.validated_data['amount']

        try:
            currency = Currency.objects.get(code=code, is_active=True)
        except Currency.DoesNotExist:
            return Response({"error": "Unsupported currency"}, status=400)

        wallet, _ = CurrencyWallet.objects.get_or_create(
            user=request.user, currency=currency
        )
        wallet.balance += amount
        wallet.save()

        CurrencyTransaction.objects.create(
            user=request.user,
            currency=currency,
            transaction_type='deposit',
            amount=amount,
            narration=f"Deposit of {code} {amount}"
        )

        return Response({
            "message": "Deposit successful",
            "currency": code,
            "new_balance": str(wallet.balance)
        })


class CurrencyWithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CurrencyWithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['currency_code'].upper()
        amount = serializer.validated_data['amount']

        try:
            currency = Currency.objects.get(code=code, is_active=True)
        except Currency.DoesNotExist:
            return Response({"error": "Unsupported currency"}, status=400)

        try:
            wallet = CurrencyWallet.objects.get(user=request.user, currency=currency)
        except CurrencyWallet.DoesNotExist:
            return Response({"error": "No wallet found for this currency"}, status=400)

        if wallet.balance < amount:
            return Response({"error": "Insufficient balance"}, status=400)

        wallet.balance -= amount
        wallet.save()

        CurrencyTransaction.objects.create(
            user=request.user,
            currency=currency,
            transaction_type='withdraw',
            amount=amount,
            narration=f"Withdrawal of {code} {amount}"
        )

        return Response({
            "message": "Withdrawal successful",
            "currency": code,
            "new_balance": str(wallet.balance)
        })


class ExchangeNgnToForeignView(APIView):
    """Convert NGN wallet balance into a foreign currency wallet."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ExchangeToForeignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['currency_code'].upper()
        ngn_amount = serializer.validated_data['ngn_amount']

        try:
            currency = Currency.objects.get(code=code, is_active=True)
        except Currency.DoesNotExist:
            return Response({"error": "Unsupported currency"}, status=400)

        try:
            rate = currency.rate.rate_to_ngn
        except ExchangeRate.DoesNotExist:
            return Response({"error": "No exchange rate available for this currency"}, status=400)

        ngn_wallet = Wallet.objects.get(user=request.user)

        if ngn_wallet.balance < ngn_amount:
            return Response({"error": "Insufficient NGN balance"}, status=400)

        foreign_amount = (ngn_amount / rate).quantize(Decimal("0.01"))

        with db_transaction.atomic():
            ngn_wallet.balance -= ngn_amount
            ngn_wallet.save()

            foreign_wallet, _ = CurrencyWallet.objects.get_or_create(
                user=request.user, currency=currency
            )
            foreign_wallet.balance += foreign_amount
            foreign_wallet.save()

            CurrencyTransaction.objects.create(
                user=request.user,
                currency=currency,
                transaction_type='exchange_in',
                amount=foreign_amount,
                rate_used=rate,
                narration=f"Exchanged ₦{ngn_amount} to {code}"
            )

        return Response({
            "message": "Exchange successful",
            "ngn_deducted": str(ngn_amount),
            "currency": code,
            "foreign_amount_credited": str(foreign_amount),
            "rate_used": str(rate),
            "new_ngn_balance": str(ngn_wallet.balance),
            "new_foreign_balance": str(foreign_wallet.balance),
        })


class ExchangeForeignToNgnView(APIView):
    """Convert a foreign currency wallet balance back into NGN."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ExchangeToNgnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['currency_code'].upper()
        foreign_amount = serializer.validated_data['foreign_amount']

        try:
            currency = Currency.objects.get(code=code, is_active=True)
        except Currency.DoesNotExist:
            return Response({"error": "Unsupported currency"}, status=400)

        try:
            rate = currency.rate.rate_to_ngn
        except ExchangeRate.DoesNotExist:
            return Response({"error": "No exchange rate available for this currency"}, status=400)

        try:
            foreign_wallet = CurrencyWallet.objects.get(user=request.user, currency=currency)
        except CurrencyWallet.DoesNotExist:
            return Response({"error": "No wallet found for this currency"}, status=400)

        if foreign_wallet.balance < foreign_amount:
            return Response({"error": "Insufficient balance in this currency"}, status=400)

        ngn_amount = (foreign_amount * rate).quantize(Decimal("0.01"))

        with db_transaction.atomic():
            foreign_wallet.balance -= foreign_amount
            foreign_wallet.save()

            ngn_wallet = Wallet.objects.get(user=request.user)
            ngn_wallet.balance += ngn_amount
            ngn_wallet.save()

            CurrencyTransaction.objects.create(
                user=request.user,
                currency=currency,
                transaction_type='exchange_out',
                amount=foreign_amount,
                rate_used=rate,
                narration=f"Exchanged {code} {foreign_amount} to ₦{ngn_amount}"
            )

        return Response({
            "message": "Exchange successful",
            "foreign_deducted": str(foreign_amount),
            "currency": code,
            "ngn_amount_credited": str(ngn_amount),
            "rate_used": str(rate),
            "new_foreign_balance": str(foreign_wallet.balance),
            "new_ngn_balance": str(ngn_wallet.balance),
        })


class CurrencyTransactionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = CurrencyTransaction.objects.filter(
            user=request.user
        ).order_by('-created_at')
        return Response(CurrencyTransactionSerializer(transactions, many=True).data)