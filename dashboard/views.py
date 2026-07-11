from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from wallet.models import Wallet,Transaction
from agent.models import Agent
from vtu.models import AirtimeTransaction, DataTransaction

User = get_user_model()


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        total_users = User.objects.count()

        total_agents = Agent.objects.count()

        total_wallets = Wallet.objects.count()

        total_balance = sum(
            wallet.balance for wallet in Wallet.objects.all()
        )

        total_transactions = Transaction.objects.count()

        airtime_sales = AirtimeTransaction.objects.count()

        data_sales = DataTransaction.objects.count()

        return Response({
            "total_users": total_users,
            "total_agents": total_agents,
            "total_wallets": total_wallets,
            "total_wallet_balance": str(total_balance),
            "total_transactions": total_transactions,
            "total_airtime_sales": airtime_sales,
            "total_data_sales": data_sales,
        })


class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        users = User.objects.all()

        data = []

        for user in users:

            try:
                wallet = Wallet.objects.get(user=user)
            except Wallet.DoesNotExist:
                continue

            data.append({
                "id": user.id,
                "username": user.username,
                "account_number": wallet.account_number,
                "balance": str(wallet.balance)
            })

        return Response(data)
    
class FreezeUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        account_number = request.data.get("account_number")

        if not account_number:
            return Response(
                {"error": "account_number is required"},
                status=400
            )

        try:
            wallet = Wallet.objects.get(
                account_number=account_number
            )
        except Wallet.DoesNotExist:
            return Response(
                {"error": "Wallet not found"},
                status=404
            )

        wallet.is_active = False
        wallet.save()

        return Response({
            "message": "User account frozen successfully",
            "username": wallet.user.username,
            "account_number": wallet.account_number,
            "status": "FROZEN"
        })
        
class UnfreezeUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        account_number = request.data.get("account_number")

        if not account_number:
            return Response(
                {"error": "account_number is required"},
                status=400
            )

        try:
            wallet = Wallet.objects.get(
                account_number=account_number
            )
        except Wallet.DoesNotExist:
            return Response(
                {"error": "Wallet not found"},
                status=404
            )

        wallet.is_active = True
        wallet.save()

        return Response({
            "message": "User account activated successfully",
            "username": wallet.user.username,
            "account_number": wallet.account_number,
            "status": "ACTIVE"
        })
        
class AgentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        agents = Agent.objects.all()

        data = []

        for agent in agents:
            data.append({
                "id": agent.id,
                "username": agent.user.username,
                "business_name": agent.business_name,
                "phone": agent.phone,
                "address": agent.address,
                "commission_balance": str(agent.commission_balance),
                "status": agent.status,
            })

        return Response(data)


class SuspendAgentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        agent_id = request.data.get("agent_id")

        if not agent_id:
            return Response(
                {"error": "agent_id is required"},
                status=400
            )

        try:
            agent = Agent.objects.get(id=agent_id)
        except Agent.DoesNotExist:
            return Response(
                {"error": "Agent not found"},
                status=404
            )

        agent.status = "SUSPENDED"
        agent.save()

        return Response({
            "message": "Agent suspended successfully",
            "agent": agent.business_name,
            "status": agent.status
        })


class ReactivateAgentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        agent_id = request.data.get("agent_id")

        if not agent_id:
            return Response(
                {"error": "agent_id is required"},
                status=400
            )

        try:
            agent = Agent.objects.get(id=agent_id)
        except Agent.DoesNotExist:
            return Response(
                {"error": "Agent not found"},
                status=404
            )

        agent.status = "ACTIVE"
        agent.save()

        return Response({
            "message": "Agent activated successfully",
            "agent": agent.business_name,
            "status": agent.status
        })
        
class TransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        transactions = Transaction.objects.all().order_by("-timestamp")

        username = request.GET.get("username")
        reference = request.GET.get("reference")
        transaction_type = request.GET.get("type")

        if username:
            transactions = transactions.filter(
                user__username__icontains=username
            )

        if reference:
            transactions = transactions.filter(
                reference__icontains=reference
            )

        if transaction_type:
            transactions = transactions.filter(
                transaction_type__iexact=transaction_type
            )

        data = []

        for transaction in transactions:

            try:
                wallet = Wallet.objects.get(user=transaction.user)
                account_number = wallet.account_number
                balance_after = str(wallet.balance)
            except Wallet.DoesNotExist:
                account_number = None
                balance_after = "0.00"

            data.append({
                "reference": transaction.reference,
                "username": transaction.user.username,
                "account_number": account_number,
                "type": transaction.transaction_type,
                "amount": str(transaction.amount),
                "balance_after": balance_after,
                "narration": transaction.narration,
                "date": transaction.timestamp,
            })

        return Response(data)
  