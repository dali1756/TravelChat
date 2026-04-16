from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from chats.models import ChatRoom, ChatRoomMember, Message


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close()
            return
        is_member = await self._check_membership(user.id, self.room_id)
        if not is_member:
            await self.close()
            return
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        msg_type = content.get("type")
        if msg_type == "message.send":
            await self._handle_message_send(content)

    async def _handle_message_send(self, content):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.send_json({"type": "error", "detail": "未授權。"})
            return
        is_member = await self._check_membership(user.id, self.room_id)
        if not is_member:
            await self.send_json({"type": "error", "detail": "您不是此聊天室的成員。"})
            return
        text = content.get("content", "").strip()
        if not text:
            await self.send_json({"type": "error", "detail": "訊息內容不能為空。"})
            return
        message = await self._persist_message(user.id, self.room_id, text)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "message.created",
                "message": {
                    "id": message["id"],
                    "sender_id": message["sender_id"],
                    "sender_username": message["sender_username"],
                    "message_type": message["message_type"],
                    "content": message["content"],
                    "created_at": message["created_at"],
                },
            },
        )

    async def message_created(self, event):
        await self.send_json(
            {
                "type": "message.created",
                "message": event["message"],
            }
        )

    @database_sync_to_async
    def _check_membership(self, user_id, room_id):
        return ChatRoomMember.objects.filter(room_id=room_id, user_id=user_id).exists()

    @database_sync_to_async
    def _persist_message(self, user_id, room_id, text):
        message = Message.objects.create(
            room_id=room_id,
            sender_id=user_id,
            message_type=Message.MessageType.TEXT,
            content=text,
        )
        ChatRoom.objects.filter(id=room_id).update(last_message_at=timezone.now())
        return {
            "id": message.id,
            "sender_id": message.sender_id,
            "sender_username": message.sender.username,
            "message_type": message.message_type,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
        }
