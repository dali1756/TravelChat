from dataclasses import dataclass
from datetime import datetime

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from chats.models import ChatRoomMember, Message


@dataclass
class ReadResult:
    advanced: bool
    last_read_message_id: int | None
    read_at: datetime


def _broadcast_message_read(*, room_id: int, user_id: int, last_read_message_id: int, read_at: datetime) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f"chat_{room_id}",
        {
            "type": "message.read",
            "room_id": room_id,
            "user_id": user_id,
            "last_read_message_id": last_read_message_id,
            "read_at": read_at.isoformat(),
        },
    )


def mark_room_read(*, room, user, message_id=None) -> ReadResult:
    with transaction.atomic():
        try:
            member = ChatRoomMember.objects.select_for_update().get(room=room, user=user)
        except ChatRoomMember.DoesNotExist as exc:
            raise PermissionDenied("您不是此聊天室的成員。") from exc

        if message_id is None:
            target = Message.objects.filter(room=room).order_by("-created_at").first()
            if target is None:
                return ReadResult(
                    advanced=False,
                    last_read_message_id=member.last_read_message_id,
                    read_at=timezone.now(),
                )
        else:
            try:
                target = Message.objects.get(id=message_id)
            except Message.DoesNotExist as exc:
                raise ValidationError({"message_id": ["訊息不存在。"]}) from exc
            if target.room_id != room.id:
                raise ValidationError({"message_id": ["訊息不屬於此聊天室。"]})

        current = member.last_read_message
        if current is not None and target.created_at <= current.created_at:
            return ReadResult(
                advanced=False,
                last_read_message_id=current.id,
                read_at=timezone.now(),
            )

        member.last_read_message = target
        member.save(update_fields=["last_read_message"])

        read_at = timezone.now()
        room_id = room.id
        user_id = user.id
        target_id = target.id
        transaction.on_commit(
            lambda: _broadcast_message_read(
                room_id=room_id,
                user_id=user_id,
                last_read_message_id=target_id,
                read_at=read_at,
            )
        )

        return ReadResult(
            advanced=True,
            last_read_message_id=target.id,
            read_at=read_at,
        )
