from decimal import Decimal
import uuid

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from wallet.models import Wallet, withdraw
from .models import AirtimeTransaction, DataTransaction, BillPayment


class BuyAirtimeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        network = request.data.get("network")
        phone_number = request.data.get("phone_number")
        amount = request.data.get("amount")

        if not network or not phone_number or not amount:
            return Response(
                {
                    "error": "network, phone_number and amount are required"
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

        wallet = Wallet.objects.get(user=request.user)

        transaction = withdraw(
            wallet,
            amount,
            narration=f"Airtime Purchase ({network})"
        )

        if transaction is None:
            return Response(
                {"error": "Insufficient wallet balance"},
                status=400
            )

        airtime = AirtimeTransaction.objects.create(
            user=request.user,
            network=network,
            phone_number=phone_number,
            amount=amount,
            reference="VTU" + uuid.uuid4().hex[:10].upper(),
            status="SUCCESS",
            provider_response="SIMULATED SUCCESS"
        )

        return Response({
            "message": "Airtime purchase successful",
            "reference": airtime.reference,
            "network": airtime.network,
            "phone_number": airtime.phone_number,
            "amount": str(airtime.amount),
            "wallet_balance": str(wallet.balance),
            "transaction_reference": transaction.reference
        })


class BuyDataView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        network = request.data.get("network")
        plan = request.data.get("plan")
        phone_number = request.data.get("phone_number")
        amount = request.data.get("amount")

        if not network or not plan or not phone_number or not amount:
            return Response(
                {
                    "error": "network, plan, phone_number and amount are required"
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

        wallet = Wallet.objects.get(user=request.user)

        transaction = withdraw(
            wallet,
            amount,
            narration=f"Data Purchase ({plan})"
        )

        if transaction is None:
            return Response(
                {"error": "Insufficient wallet balance"},
                status=400
            )

        data = DataTransaction.objects.create(
            user=request.user,
            network=network,
            plan=plan,
            phone_number=phone_number,
            amount=amount,
            reference="DATA" + uuid.uuid4().hex[:10].upper(),
            status="SUCCESS",
            provider_response="SIMULATED SUCCESS"
        )

        return Response({
            "message": "Data purchase successful",
            "reference": data.reference,
            "network": data.network,
            "plan": data.plan,
            "phone_number": data.phone_number,
            "amount": str(data.amount),
            "wallet_balance": str(wallet.balance),
            "transaction_reference": transaction.reference
        })
        
class PayBillView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        bill_type = request.data.get("bill_type")
        provider = request.data.get("provider")
        customer_number = request.data.get("customer_number")
        amount = request.data.get("amount")

        if not bill_type or not provider or not customer_number or not amount:
            return Response(
                {
                    "error": "bill_type, provider, customer_number and amount are required"
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

        wallet = Wallet.objects.get(user=request.user)

        transaction = withdraw(
            wallet,
            amount,
            narration=f"{bill_type} Bill Payment"
        )

        if transaction is None:
            return Response(
                {"error": "Insufficient wallet balance"},
                status=400
            )

        bill = BillPayment.objects.create(
            user=request.user,
            bill_type=bill_type,
            provider=provider,
            customer_number=customer_number,
            amount=amount,
            reference="BILL" + uuid.uuid4().hex[:10].upper(),
            status="SUCCESS",
            provider_response="SIMULATED SUCCESS"
        )

        return Response({
            "message": "Bill payment successful",
            "reference": bill.reference,
            "bill_type": bill.bill_type,
            "provider": bill.provider,
            "customer_number": bill.customer_number,
            "amount": str(bill.amount),
            "wallet_balance": str(wallet.balance),
            "transaction_reference": transaction.reference
        })
