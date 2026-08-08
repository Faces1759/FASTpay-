from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Wallet, Transaction


@api_view(['POST'])
def deposit_view(request):
    user_id = request.data.get('user_id')
    amount = request.data.get('amount')

    if not user_id or not amount:
        return Response({"error": "user_id and amount are required"})

    try:
        amount = float(amount)
        wallet = Wallet.objects.get(user_id=user_id)

        wallet.balance += amount
        wallet.save()

        Transaction.objects.create(
            user=wallet.user,
            amount=amount,
            transaction_type='deposit'
        )

        return Response({
            "message": "Deposit successful",
            "new_balance": wallet.balance
        })

    except Wallet.DoesNotExist:
        return Response({"error": "Wallet not found"})


@api_view(['POST'])
def withdraw_view(request):
    user_id = request.data.get('user_id')
    amount = request.data.get('amount')

    if not user_id or not amount:
        return Response({"error": "user_id and amount are required"})

    try:
        amount = float(amount)
        wallet = Wallet.objects.get(user_id=user_id)

        if wallet.balance < amount:
            return Response({"error": "Insufficient balance"})

        wallet.balance -= amount
        wallet.save()

        Transaction.objects.create(
            user=wallet.user,
            amount=amount,
            transaction_type='withdraw'
        )

        return Response({
            "message": "Withdrawal successful",
            "new_balance": wallet.balance
        })

    except Wallet.DoesNotExist:
        return Response({"error": "Wallet not found"})