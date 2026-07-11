from decimal import Decimal

from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Agent
from wallet.models import Wallet, deposit, withdraw

User = get_user_model()


class RegisterAgentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        if Agent.objects.filter(user=request.user).exists():
            return Response(
                {"error": "You are already registered as an agent"},
                status=400
            )

        business_name = request.data.get("business_name")
        phone = request.data.get("phone")
        address = request.data.get("address")

        if not business_name or not phone or not address:
            return Response(
                {
                    "error": "business_name, phone and address are required"
                },
                status=400
            )

        agent = Agent.objects.create(
            user=request.user,
            business_name=business_name,
            phone=phone,
            address=address
        )

        return Response({
            "message": "Agent registered successfully",
            "business_name": agent.business_name,
            "status": agent.status
        })


class AgentProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        agent = Agent.objects.get(user=request.user)

        return Response({
            "business_name": agent.business_name,
            "phone": agent.phone,
            "address": agent.address,
            "commission_balance": str(agent.commission_balance),
            "status": agent.status
        })


class AgentDepositView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        account_number = request.data.get("account_number")
        amount = request.data.get("amount")

        if not account_number or not amount:
            return Response(
                {
                    "error": "account_number and amount are required"
                },
                status=400
            )

        try:
            amount = Decimal(str(amount))
        except:
            return Response(
                {"error": "Invalid amount"},
                status=400
            )

        # Check if the agent is active
        agent = Agent.objects.get(user=request.user)

        if agent.status != "ACTIVE":
            return Response(
                {
                    "error": "This agent has been suspended."
                },
                status=403
            )

        try:
            wallet = Wallet.objects.get(
                account_number=account_number
            )
        except Wallet.DoesNotExist:
            return Response(
                {"error": "Account not found"},
                status=404
            )

        transaction = deposit(
            wallet,
            amount,
            narration="Cash Deposit by FASTpay Agent"
        )

        agent.commission_balance += Decimal("10")
        agent.save()

        return Response({
            "message": "Deposit successful",
            "customer": wallet.user.username,
            "account_number": wallet.account_number,
            "amount": str(amount),
            "reference": transaction.reference,
            "wallet_balance": str(wallet.balance),
            "agent_commission": str(agent.commission_balance)
        })


class AgentWithdrawalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        account_number = request.data.get("account_number")
        amount = request.data.get("amount")

        if not account_number or not amount:
            return Response(
                {
                    "error": "account_number and amount are required"
                },
                status=400
            )

        try:
            amount = Decimal(str(amount))
        except:
            return Response(
                {"error": "Invalid amount"},
                status=400
            )

        # Check if the agent is active
        agent = Agent.objects.get(user=request.user)

        if agent.status != "ACTIVE":
            return Response(
                {
                    "error": "This agent has been suspended."
                },
                status=403
            )

        try:
            wallet = Wallet.objects.get(
                account_number=account_number
            )
        except Wallet.DoesNotExist:
            return Response(
                {"error": "Account not found"},
                status=404
            )

        transaction = withdraw(
            wallet,
            amount,
            narration="Cash Withdrawal by FASTpay Agent"
        )

        if transaction is None:
            return Response(
                {"error": "Insufficient wallet balance"},
                status=400
            )

        agent.commission_balance += Decimal("10")
        agent.save()

        return Response({
            "message": "Withdrawal successful",
            "customer": wallet.user.username,
            "account_number": wallet.account_number,
            "amount": str(amount),
            "reference": transaction.reference,
            "wallet_balance": str(wallet.balance),
            "agent_commission": str(agent.commission_balance)
        })