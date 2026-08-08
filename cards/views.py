from decimal import Decimal
import random

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from wallet.models import Wallet
from .models import VirtualCard


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
            "status": card.status
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
            "status": card.status
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

        card.status = "BLOCKED"
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