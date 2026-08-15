from decimal import Decimal
import random
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from wallet.models import Wallet
from .models import VirtualCard, CardTransaction


class CreateVirtualCardView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        if VirtualCard.objects.filter(user=request.user).exists():
            return Response(
                {"error": "You already have a virtual card"},
                status=400
            )
        card = VirtualCard.objects.create(
            user=request.user,
            card_holder=request.user.username.upper(),
            card_number="5399" + "".join(
                [str(random.randint(0, 9)) for _ in range(12)]
            ),
            expiry="12/30",
            cvv=str(random.randint(100, 999))
        )
        return Response({
            "message": "Virtual card created successfully",
            "card_holder": card.card_holder,
            "card_number": card.card_number,
            "expiry": card.expiry,
            "cvv": card.cvv,
            "balance": str(card.balance),
            "status": card.status,
            "online_enabled": card.online_enabled,
            "offline_enabled": card.offline_enabled
        })


class CardDetailsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        card = VirtualCard.objects.get(user=request.user)
        return Response({
            "card_holder": card.card_holder,
            "card_number": card.card_number,
            "expiry": card.expiry,
            "balance": str(card.balance),
            "status": card.status,
            "online_enabled": card.online_enabled,
            "offline_enabled": card.offline_enabled
        })


class FundCardView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        amount = request.data.get("amount")
        if not amount:
            return Response(
                {"error": "Amount is required"},
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
        card = VirtualCard.objects.get(user=request.user)
        if wallet.balance < amount:
            return Response(
                {"error": "Insufficient wallet balance"},
                status=400
            )
        wallet.balance -= amount
        wallet.save()
        card.balance += amount
        card.save()
        return Response({
            "message": "Card funded successfully",
            "wallet_balance": str(wallet.balance),
            "card_balance": str(card.balance)
        })


class FreezeCardView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        card = VirtualCard.objects.get(user=request.user)
        card.status = "FROZEN"
        card.save()
        return Response({
            "message": "Card frozen successfully",
            "status": card.status
        })


class UnfreezeCardView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        card = VirtualCard.objects.get(user=request.user)
        card.status = "ACTIVE"
        card.save()
        return Response({
            "message": "Card activated successfully",
            "status": card.status
        })


class ToggleOnlineView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        card = VirtualCard.objects.get(user=request.user)
        card.online_enabled = not card.online_enabled
        card.save()
        return Response({
            "message": "Online payments enabled" if card.online_enabled else "Online payments disabled",
            "online_enabled": card.online_enabled
        })


class ToggleOfflineView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        card = VirtualCard.objects.get(user=request.user)
        card.offline_enabled = not card.offline_enabled
        card.save()
        return Response({
            "message": "Offline/POS payments enabled" if card.offline_enabled else "Offline/POS payments disabled",
            "offline_enabled": card.offline_enabled
        })


class CardPOSTransactionView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        amount = request.data.get("amount")
        account_type = request.data.get("account_type", "savings")
        channel = request.data.get("channel", "pos")

        if not amount:
            return Response({"error": "Amount is required"}, status=400)

        try:
            amount = Decimal(str(amount))
        except:
            return Response({"error": "Invalid amount"}, status=400)

        if amount <= 0:
            return Response({"error": "Amount must be greater than 0"}, status=400)

        if account_type not in ("savings", "current"):
            return Response({"error": "account_type must be savings or current"}, status=400)

        try:
            card = VirtualCard.objects.get(user=request.user)
        except VirtualCard.DoesNotExist:
            return Response({"error": "No virtual card found"}, status=404)

        if card.status != "ACTIVE":
            return Response({"error": "Card is frozen"}, status=400)

        if channel == "online" and not card.online_enabled:
            return Response({"error": "Online payments are disabled for this card"}, status=400)

        if channel == "pos" and not card.offline_enabled:
            return Response({"error": "Offline/POS payments are disabled for this card"}, status=400)

        reference = "CARD-" + uuid.uuid4().hex[:12].upper()

        if card.balance < amount:
            CardTransaction.objects.create(
                card=card,
                amount=amount,
                account_type=account_type,
                channel=channel,
                status="failed",
                reference=reference
            )
            return Response({"error": "Insufficient card balance"}, status=400)

        card.balance -= amount
        card.save()

        CardTransaction.objects.create(
            card=card,
            amount=amount,
            account_type=account_type,
            channel=channel,
            status="success",
            reference=reference
        )

        return Response({
            "message": "Transaction successful",
            "reference": reference,
            "amount": str(amount),
            "account_type": account_type,
            "channel": channel,
            "card_balance": str(card.balance)
        })


class CardTransactionHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        card = VirtualCard.objects.get(user=request.user)
        transactions = card.transactions.all().order_by("-id")
        data = []
        for t in transactions:
            data.append({
                "reference": t.reference,
                "amount": str(t.amount),
                "account_type": t.account_type,
                "channel": t.channel,
                "status": t.status,
                "date": t.created_at
            })
        return Response(data)