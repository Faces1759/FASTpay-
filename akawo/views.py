from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from django.db.models import Sum
from .models import AkawoGroup, AkawoMember, AkawoContribution, AkawoPayout
from .serializers import (
    AkawoGroupSerializer,
    AkawoMemberSerializer,
    ContributionSerializer,
    AkawoPayoutSerializer,
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