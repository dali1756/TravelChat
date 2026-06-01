from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from chats.ai import get_provider
from chats.ai.prompts import TRAVEL_PLANNING_SYSTEM_PROMPT
from chats.models import AIConversation, AIMessage, ChatRoom, ChatRoomMember, Message
from chats.services import mark_room_read


def _next_chunk(generator):
    """
    在 thread 中步進同步產生器，回傳(chunk, done)。
    """
    try:
        return next(generator), False
    except StopIteration:
        return None, True


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
        elif msg_type == "message.read":
            await self._handle_message_read(content)

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

    async def message_read(self, event):
        await self.send_json(
            {
                "type": "message.read",
                "room_id": event["room_id"],
                "user_id": event["user_id"],
                "last_read_message_id": event["last_read_message_id"],
                "read_at": event["read_at"],
            }
        )

    async def _handle_message_read(self, content):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.send_json({"type": "error", "detail": "未授權。"})
            return
        message_id = content.get("message_id")
        try:
            await self._mark_read(user, self.room_id, message_id)
        except PermissionDenied as exc:
            await self.send_json({"type": "error", "detail": str(exc)})
        except ValidationError as exc:
            await self.send_json({"type": "error", "detail": str(exc)})

    @database_sync_to_async
    def _mark_read(self, user, room_id, message_id):
        room = ChatRoom.objects.get(id=room_id)
        return mark_room_read(room=room, user=user, message_id=message_id)

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


class AIConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close()
            return
        if not await self._is_owner(user.id, self.conversation_id):
            await self.close()
            return
        await self.accept()

    async def receive_json(self, content, **kwargs):
        if content.get("type") != "ai.message":
            return
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.send_json({"type": "error", "detail": "未授權。"})
            return
        if not await self._is_owner(user.id, self.conversation_id):
            await self.send_json({"type": "error", "detail": "您不是此對話的擁有者。"})
            return
        text = (content.get("content") or "").strip()
        if not text:
            await self.send_json({"type": "error", "detail": "訊息內容不能為空。"})
            return
        await self._persist_message(AIMessage.Role.USER, text)
        history = await self._load_history()
        provider = get_provider()
        parts = []
        try:
            generator = provider.stream(history, TRAVEL_PLANNING_SYSTEM_PROMPT)
            while True:
                chunk, done = await sync_to_async(_next_chunk)(generator)
                if done:
                    break
                parts.append(chunk)
                await self.send_json({"type": "ai.chunk", "delta": chunk})
        except Exception:
            await self.send_json({"type": "error", "detail": "AI 服務暫時無法回應，請稍後再試。"})
            return
        full = "".join(parts)
        message_id = await self._persist_message(AIMessage.Role.MODEL, full)
        await self.send_json({"type": "ai.done", "message_id": message_id, "content": full})

    @database_sync_to_async
    def _is_owner(self, user_id, conversation_id):
        return AIConversation.objects.filter(id=conversation_id, owner_id=user_id).exists()

    @database_sync_to_async
    def _persist_message(self, role, content):
        message = AIMessage.objects.create(
            conversation_id=self.conversation_id,
            role=role,
            content=content,
        )
        AIConversation.objects.filter(id=self.conversation_id).update(updated_at=timezone.now())
        return message.id

    @database_sync_to_async
    def _load_history(self):
        return [
            {"role": m.role, "content": m.content}
            for m in AIMessage.objects.filter(conversation_id=self.conversation_id)
        ]
