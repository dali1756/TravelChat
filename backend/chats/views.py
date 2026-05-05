from datetime import datetime
from datetime import timezone as dt_timezone

from django.db import IntegrityError, transaction
from django.db.models import Count, IntegerField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from chats.models import ChatRoom, ChatRoomMember, Message
from chats.serializers import (
    ChatRoomListSerializer,
    DirectRoomCreateSerializer,
    GroupRoomCreateSerializer,
    MarkRoomReadSerializer,
    MessageSerializer,
    RoomMemberAddSerializer,
    RoomMemberSerializer,
)
from chats.services import mark_room_read
from members.models import User

_EPOCH = datetime(1970, 1, 1, tzinfo=dt_timezone.utc)


class DirectRoomCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DirectRoomCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        peer_user_id = serializer.validated_data["peer_user_id"]
        current_user = request.user
        peer_user = User.objects.public().get(id=peer_user_id)
        direct_key = ChatRoom.make_direct_key(current_user.id, peer_user.id)
        created = False
        try:
            with transaction.atomic():
                room = ChatRoom.objects.create(
                    room_type=ChatRoom.RoomType.DIRECT,
                    direct_key=direct_key,
                    created_by=current_user,
                )
                ChatRoomMember.objects.create(room=room, user=current_user)
                ChatRoomMember.objects.create(room=room, user=peer_user)
                created = True
        except IntegrityError:
            room = ChatRoom.objects.get(direct_key=direct_key)
        response_serializer = ChatRoomListSerializer(room, context={"request": request})
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(response_serializer.data, status=response_status)


class ChatRoomListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatRoomListSerializer

    def get_queryset(self):
        user = self.request.user
        my_last_read_at = Subquery(
            ChatRoomMember.objects.filter(
                room=OuterRef("pk"),
                user=user,
            ).values("last_read_message__created_at")[:1]
        )
        unread_count_sq = Subquery(
            Message.objects.filter(room=OuterRef("pk"))
            .exclude(sender=user)
            .filter(created_at__gt=OuterRef("_my_last_read_at"))
            .values("room")
            .annotate(c=Count("id"))
            .values("c"),
            output_field=IntegerField(),
        )
        return (
            ChatRoom.objects.filter(members__user=user)
            .annotate(_my_last_read_at=Coalesce(my_last_read_at, Value(_EPOCH)))
            .annotate(unread_count=Coalesce(unread_count_sq, Value(0)))
            .distinct()
        )


class MessageHistoryView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        room_id = self.kwargs["room_id"]
        user = self.request.user
        if not ChatRoomMember.objects.filter(room_id=room_id, user=user).exists():
            return Message.objects.none()
        return Message.objects.filter(room_id=room_id).select_related("sender")

    def list(self, request, *args, **kwargs):
        room_id = self.kwargs["room_id"]
        if not ChatRoomMember.objects.filter(room_id=room_id, user=request.user).exists():
            return Response({"detail": "您不是此聊天室的成員。"}, status=status.HTTP_403_FORBIDDEN)
        return super().list(request, *args, **kwargs)


class GroupRoomCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupRoomCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = serializer.validated_data["name"]
        member_ids = serializer.validated_data.get("member_ids", [])
        creator = request.user
        room = ChatRoom.objects.create(
            room_type=ChatRoom.RoomType.GROUP,
            name=name,
            created_by=creator,
        )
        ChatRoomMember.objects.create(room=room, user=creator)
        for uid in member_ids:
            if uid != creator.id:
                ChatRoomMember.objects.get_or_create(room=room, user_id=uid)
        response_serializer = ChatRoomListSerializer(room, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class RoomMembersView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_group_room_or_403(self, room_id, user):
        try:
            room = ChatRoom.objects.get(id=room_id)
        except ChatRoom.DoesNotExist:
            return None, Response({"detail": "聊天室不存在。"}, status=status.HTTP_404_NOT_FOUND)
        if not ChatRoomMember.objects.filter(room=room, user=user).exists():
            return None, Response({"detail": "您不是此聊天室的成員。"}, status=status.HTTP_403_FORBIDDEN)
        return room, None

    def get(self, request, room_id):
        room, err = self._get_group_room_or_403(room_id, request.user)
        if err:
            return err
        members = ChatRoomMember.objects.filter(room=room).select_related("user")
        serializer = RoomMemberSerializer(members, many=True)
        return Response(serializer.data)

    def post(self, request, room_id):
        room, err = self._get_group_room_or_403(room_id, request.user)
        if err:
            return err
        if room.room_type != ChatRoom.RoomType.GROUP:
            return Response({"detail": "只有群組聊天室支援新增成員。"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = RoomMemberAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data["user_id"]
        member, created = ChatRoomMember.objects.get_or_create(room=room, user_id=user_id)
        response_serializer = RoomMemberSerializer(member)
        if created:
            response_status = status.HTTP_201_CREATED
        else:
            response_status = status.HTTP_200_OK
        return Response(response_serializer.data, status=response_status)


class RoomMemberRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, room_id, user_id):
        try:
            room = ChatRoom.objects.get(id=room_id)
        except ChatRoom.DoesNotExist:
            return Response({"detail": "聊天室不存在。"}, status=status.HTTP_404_NOT_FOUND)
        if room.room_type != ChatRoom.RoomType.GROUP:
            return Response({"detail": "只有群組聊天室支援移除成員。"}, status=status.HTTP_400_BAD_REQUEST)
        requester = request.user
        if not ChatRoomMember.objects.filter(room=room, user=requester).exists():
            return Response({"detail": "您不是此聊天室的成員。"}, status=status.HTTP_403_FORBIDDEN)
        if requester.id != user_id and room.created_by_id != requester.id:
            return Response({"detail": "只有建立者可以移除其他成員。"}, status=status.HTTP_403_FORBIDDEN)
        try:
            target_member = ChatRoomMember.objects.get(room=room, user_id=user_id)
        except ChatRoomMember.DoesNotExist:
            return Response({"detail": "目標成員不存在。"}, status=status.HTTP_404_NOT_FOUND)
        target_member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MarkRoomReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, room_id):
        try:
            room = ChatRoom.objects.get(id=room_id)
        except ChatRoom.DoesNotExist:
            return Response({"detail": "聊天室不存在。"}, status=status.HTTP_404_NOT_FOUND)
        serializer = MarkRoomReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message_id = serializer.validated_data.get("message_id")
        result = mark_room_read(room=room, user=request.user, message_id=message_id)
        return Response(
            {
                "advanced": result.advanced,
                "last_read_message_id": result.last_read_message_id,
                "read_at": result.read_at.isoformat(),
            },
            status=status.HTTP_200_OK,
        )
