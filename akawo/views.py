from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from .models import AkawoGroup, AkawoMember, AkawoContribution, AkawoPayout, WithdrawalCode, CorporateAccount, ReleaseRequest, ReleaseApproval
from .serializers import (
    AkawoGroupSerializer,
    AkawoMemberSerializer,
    ContributionSerializer,
    AkawoPayoutSerializer,
    WithdrawalCodeGenerateSerializer,
    WithdrawalCodeSerializer,
    WithdrawalCodeRedeemSerializer,
    ReleaseRequestInitSerializer,
    ReleaseApprovalSerializer,
    ReleaseRequestSerializer,
    CorporateAccountSerializer,
)
from wallet.models import Wallet


class CreateAkawoGroupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AkawoGroupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                creator=request.user,
                current_members=1
            )
            return Response({
                "message": "Akawo group created successfully",
                "group": serializer.data
            }, status=201)
        return Response(serializer.errors, status=400)


class JoinAkawoGroupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        group_id = request.data.get("group_id")
        try:
            group = AkawoGroup.objects.get(id=group_id)
        except AkawoGroup.DoesNotExist:
            return Response(
                {"error": "Akawo group not found"},
                status=404
            )
        if AkawoMember.objects.filter(
            group=group,
            user=request.user
        ).exists():
            return Response(
                {"error": "You are already a member"},
                status=400
            )
        if group.current_members >= group.max_members:
            return Response(
                {"error": "Group is already full"},
                status=400
            )
        AkawoMember.objects.create(
            group=group,
            user=request.user
        )
        group.current_members += 1
        group.save()
        return Response({
            "message": "Successfully joined Akawo group",
            "group_name": group.name,
            "current_members": group.current_members
        })


class AkawoGroupListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        groups = AkawoGroup.objects.all()
        serializer = AkawoGroupSerializer(groups, many=True)
        return Response(serializer.data)


class MyGroupsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = AkawoMember.objects.filter(user=request.user)
        groups = [member.group for member in memberships]
        serializer = AkawoGroupSerializer(groups, many=True)
        return Response(serializer.data)


class ContributionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        group_id = request.data.get("group_id")

        try:
            group = AkawoGroup.objects.get(id=group_id)
        except AkawoGroup.DoesNotExist:
            return Response(
                {"error": "Group not found"},
                status=404
            )

        try:
            member = AkawoMember.objects.get(
                group=group,
                user=request.user
            )
        except AkawoMember.DoesNotExist:
            return Response(
                {"error": "You are not a member of this group"},
                status=400
            )

        already_paid = AkawoContribution.objects.filter(
            member=member,
            cycle_number=group.current_cycle,
            status="successful"
        ).exists()

        if already_paid:
            return Response(
                {"error": "You have already contributed for this cycle."},
                status=400
            )

        amount = group.contribution_amount

        contribution = AkawoContribution.objects.create(
            member=member,
            amount=Decimal(amount),
            cycle_number=group.current_cycle
        )

        return Response({
            "message": "Contribution successful",
            "cycle": group.current_cycle,
            "amount": contribution.amount
        })


class ContributionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        try:
            group = AkawoGroup.objects.get(id=group_id)
        except AkawoGroup.DoesNotExist:
            return Response(
                {"error": "Group not found"},
                status=404
            )

        member = AkawoMember.objects.filter(
            group=group,
            user=request.user
        ).first()

        if not member:
            return Response(
                {"error": "Not a member"},
                status=400
            )

        contributions = AkawoContribution.objects.filter(
            member__group=group
        ).order_by("-id")

        serializer = ContributionSerializer(contributions, many=True)
        return Response(serializer.data)


class GroupBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        try:
            group = AkawoGroup.objects.get(id=group_id)
        except AkawoGroup.DoesNotExist:
            return Response(
                {"error": "Group not found"},
                status=404
            )

        member = AkawoMember.objects.filter(
            group=group,
            user=request.user
        ).first()

        if not member:
            return Response(
                {"error": "You are not a member of this group"},
                status=400
            )

        total = AkawoContribution.objects.filter(
            member__group=group,
            status="successful",
            cycle_number=group.current_cycle
        ).aggregate(total=Sum("amount"))["total"] or 0

        return Response({
            "group": group.name,
            "total_balance": total
        })


class CurrentReceiverView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        try:
            group = AkawoGroup.objects.get(id=group_id)
        except AkawoGroup.DoesNotExist:
            return Response(
                {"error": "Group not found"},
                status=404
            )

        members = AkawoMember.objects.filter(group=group).order_by("joined_at")

        if not members.exists():
            return Response(
                {"error": "No members in this group"},
                status=400
            )

        current_member = members[group.current_receiver_index]

        return Response({
            "current_receiver": current_member.user.username,
            "position": group.current_receiver_index + 1,
            "total_members": members.count()
        })


class PayoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        try:
            group = AkawoGroup.objects.get(id=group_id)
        except AkawoGroup.DoesNotExist:
            return Response({"error": "Group not found"}, status=404)

        members = AkawoMember.objects.filter(group=group)
        members_count = members.count()

        if members_count == 0:
            return Response({"error": "No members in group"}, status=400)

        paid_members = AkawoContribution.objects.filter(
            member__group=group,
            cycle_number=group.current_cycle,
            status="successful"
        ).values("member").distinct().count()

        if paid_members < members_count:
            return Response(
                {
                    "error": f"Only {paid_members} of {members_count} members have contributed for this cycle."
                },
                status=400
            )

        receiver = members[group.current_receiver_index]

        if receiver.user != request.user:
            return Response({"error": "It is not your turn"}, status=403)

        total_balance = (
            AkawoContribution.objects.filter(
                member__group=group,
                cycle_number=group.current_cycle,
                status="successful"
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        wallet = Wallet.objects.get(user=request.user)
        wallet.balance += total_balance
        wallet.save()

        AkawoPayout.objects.create(
            group=group,
            member=receiver,
            amount=total_balance
        )

        group.current_receiver_index += 1

        if group.current_receiver_index >= members_count:
            group.current_receiver_index = 0
            group.current_cycle += 1

        group.save()

        return Response({
            "message": "Payout successful",
            "receiver": receiver.user.username,
            "cycle": group.current_cycle,
            "amount": total_balance,
            "new_wallet_balance": wallet.balance,
            "next_receiver_position": group.current_receiver_index + 1,
        })


class PayoutHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        try:
            group = AkawoGroup.objects.get(id=group_id)
        except AkawoGroup.DoesNotExist:
            return Response(
                {"error": "Group not found"},
                status=404
            )

        payouts = AkawoPayout.objects.filter(
            group=group
        ).order_by("-paid_at")

        serializer = AkawoPayoutSerializer(payouts, many=True)
        return Response(serializer.data)


class GenerateWithdrawalCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WithdrawalCodeGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data['amount']

        wallet = Wallet.objects.get(user=request.user)

        try:
            wallet.hold_funds(amount)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        wc = WithdrawalCode.objects.create(user=request.user, amount=amount)
        return Response(WithdrawalCodeSerializer(wc).data, status=201)


class RedeemWithdrawalCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WithdrawalCodeRedeemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code']
        agent_id = serializer.validated_data.get('agent_id', '')

        try:
            wc = WithdrawalCode.objects.get(code=code)
        except WithdrawalCode.DoesNotExist:
            return Response({"error": "Invalid code"}, status=404)

        if wc.status != 'pending':
            return Response({"error": f"Code already {wc.status}"}, status=400)

        wallet = Wallet.objects.get(user=wc.user)

        if wc.is_expired():
            wc.status = 'expired'
            wc.save()
            wallet.release_funds(wc.amount)
            return Response({"error": "Code expired"}, status=400)

        wallet.deduct_held_funds(wc.amount)
        wc.status = 'used'
        wc.redeemed_at = timezone.now()
        wc.redeemed_by_agent = agent_id
        wc.save()

        return Response({"message": "Withdrawal successful", "amount": str(wc.amount)})


class MyWithdrawalCodesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        codes = WithdrawalCode.objects.filter(user=request.user).order_by('-created_at')
        return Response(WithdrawalCodeSerializer(codes, many=True).data)

class CreateCorporateAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if CorporateAccount.objects.filter(user=request.user).exists():
            return Response({"error": "Corporate account already exists"}, status=400)

        serializer = CorporateAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)


class InitiateReleaseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReleaseRequestInitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            corp = CorporateAccount.objects.get(user=request.user)
        except CorporateAccount.DoesNotExist:
            return Response({"error": "No corporate account found"}, status=404)

        if not corp.is_authorized(data['initiator_number']):
            return Response({"error": "Number not authorized"}, status=403)

        wallet = Wallet.objects.get(user=request.user)
        if wallet.available_balance() < data['amount']:
            return Response({"error": "Insufficient available balance"}, status=400)

        wallet.hold_funds(data['amount'])

        rr = ReleaseRequest.objects.create(
            corporate_account=corp,
            amount=data['amount'],
            reason=data.get('reason', ''),
            initiated_by=data['initiator_number'],
        )
        ReleaseApproval.objects.create(request=rr, phone_number=data['initiator_number'], approved=True)

        return Response(ReleaseRequestSerializer(rr).data, status=201)


class ApproveReleaseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReleaseApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            rr = ReleaseRequest.objects.get(id=data['request_id'])
        except ReleaseRequest.DoesNotExist:
            return Response({"error": "Request not found"}, status=404)

        corp = rr.corporate_account

        if not corp.is_authorized(data['phone_number']):
            return Response({"error": "Number not authorized"}, status=403)

        if rr.status != 'pending':
            return Response({"error": f"Request already {rr.status}"}, status=400)

        wallet = Wallet.objects.get(user=corp.user)

        if rr.is_expired():
            rr.status = 'expired'
            rr.save()
            wallet.release_funds(rr.amount)
            return Response({"error": "Request expired"}, status=400)

        if ReleaseApproval.objects.filter(request=rr, phone_number=data['phone_number']).exists():
            return Response({"error": "This number already responded"}, status=400)

        ReleaseApproval.objects.create(
            request=rr, phone_number=data['phone_number'], approved=data['approved']
        )

        if not data['approved']:
            rr.status = 'rejected'
            rr.resolved_at = timezone.now()
            rr.save()
            wallet.release_funds(rr.amount)
            return Response({"message": "Request rejected. Funds unlocked."})

        approvals_count = rr.approvals.filter(approved=True).count()
        if approvals_count >= 3:
            wallet.deduct_held_funds(rr.amount)
            rr.status = 'approved'
            rr.resolved_at = timezone.now()
            rr.save()
            return Response({"message": "Fully approved. Funds released.", "amount": str(rr.amount)})

        return Response({
            "message": f"Approval recorded ({approvals_count}/3). Waiting for remaining approvals.",
        })


class ReleaseRequestStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, request_id):
        try:
            rr = ReleaseRequest.objects.get(id=request_id)
        except ReleaseRequest.DoesNotExist:
            return Response({"error": "Not found"}, status=404)
        return Response(ReleaseRequestSerializer(rr).data)