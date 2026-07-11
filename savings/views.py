from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import (
    SavingsPlan,
    SavingsDeposit,
    SavingsWithdrawal,
)
from .serializers import SavingsPlanSerializer
from wallet.models import Wallet

class CreateSavingsPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SavingsPlanSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        wallet = Wallet.objects.get(user=request.user)

        first_deposit = Decimal(
            str(serializer.validated_data["amount_per_deposit"])
        )

        if wallet.balance < first_deposit:
            return Response(
                {"error": "Insufficient wallet balance"},
                status=400
            )

        # Deduct first deposit from wallet
        wallet.balance -= first_deposit
        wallet.save()

        # Create savings plan with the first deposit already inside it
        plan = serializer.save(
            user=request.user,
            current_balance=first_deposit,
            status="active"
        )

        # Save deposit history
        SavingsDeposit.objects.create(
            plan=plan,
            amount=first_deposit
        )

        return Response(
            {
                "message": "Savings plan created successfully",
                "wallet_balance": str(wallet.balance),
                "savings_balance": str(plan.current_balance),
                "plan": SavingsPlanSerializer(plan).data,
            },
            status=201,
        )
class SavingsPlanListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        plans = SavingsPlan.objects.filter(user=request.user)
        serializer = SavingsPlanSerializer(plans, many=True)
        return Response(serializer.data)

class DepositToSavingsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, plan_id):
        try:
            plan = SavingsPlan.objects.get(
                id=plan_id,
                user=request.user
            )
        except SavingsPlan.DoesNotExist:
            return Response(
                {"error": "Savings plan not found"},
                status=404
            )

        # Stop deposits if savings has been completed
        if plan.status == "completed":
            return Response(
                {"error": "This savings plan has already been completed."},
                status=400
            )

        amount = request.data.get("amount")

        if not amount:
            return Response(
                {"error": "Amount is required"},
                status=400
            )

        amount = Decimal(str(amount))

        wallet = Wallet.objects.get(user=request.user)

        if wallet.balance < amount:
            return Response(
                {"error": "Insufficient wallet balance"},
                status=400
            )

        # Deduct from wallet
        wallet.balance -= amount
        wallet.save()

        # Add to savings
        plan.current_balance += amount

        # Automatically complete the plan
        if plan.current_balance >= plan.target_amount:
            plan.current_balance = plan.target_amount
            plan.status = "completed"

        plan.save()

        # Save deposit history
        SavingsDeposit.objects.create(
            plan=plan,
            amount=amount
        )

        return Response({
            "message": "Deposit successful",
            "wallet_balance": str(wallet.balance),
            "savings_balance": str(plan.current_balance),
            "status": plan.status
        })

from decimal import Decimal, InvalidOperation

class SavingsWithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, plan_id):
        try:
            plan = SavingsPlan.objects.get(
                id=plan_id,
                user=request.user
            )
        except SavingsPlan.DoesNotExist:
            return Response(
                {"error": "Savings plan not found"},
                status=404
            )

        amount = request.data.get("amount")

        if not amount:
            return Response(
                {"error": "Amount is required"},
                status=400
            )

        try:
            amount = Decimal(str(amount))
        except InvalidOperation:
            return Response(
                {"error": "Invalid amount"},
                status=400
            )

        # Make sure current_balance is Decimal
        plan.current_balance = Decimal(str(plan.current_balance))

        # Debug (check your terminal)
        print("Current Savings Balance:", plan.current_balance)
        print("Requested Withdrawal:", amount)

        if plan.current_balance < amount:
            return Response(
                {
                    "error": "Insufficient savings balance",
                    "current_balance": str(plan.current_balance)
                },
                status=400
            )

        wallet = Wallet.objects.get(user=request.user)

        plan.current_balance -= amount

        if plan.current_balance <= 0:
            plan.current_balance = Decimal("0.00")
            plan.status = "completed"

        plan.save()

        wallet.balance += amount
        wallet.save()

        SavingsWithdrawal.objects.create(
            plan=plan,
            amount=amount
        )

        return Response({
            "message": "Withdrawal successful",
            "amount": str(amount),
            "wallet_balance": str(wallet.balance),
            "savings_balance": str(plan.current_balance),
            "status": plan.status
        })

class SavingsPlanDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, plan_id):
        try:
            plan = SavingsPlan.objects.get(
                id=plan_id,
                user=request.user
            )
        except SavingsPlan.DoesNotExist:
            return Response(
                {"error": "Savings plan not found"},
                status=404
            )

        serializer = SavingsPlanSerializer(plan)
        return Response(serializer.data)