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
    MarkRoomReadSerializer,
    MessageSerializer,
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
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


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
