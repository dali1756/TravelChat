from django.db import IntegrityError, transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from chats.models import ChatRoom, ChatRoomMember, Message
from chats.serializers import (
    ChatRoomListSerializer,
    DirectRoomCreateSerializer,
    MessageSerializer,
)
from members.models import User


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
        return ChatRoom.objects.filter(
            members__user=self.request.user,
        ).distinct()


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
