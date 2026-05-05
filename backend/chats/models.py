from django.conf import settings
from django.db import models


class ChatRoom(models.Model):
    class RoomType(models.TextChoices):
        DIRECT = "direct", "Direct"
        GROUP = "group", "Group"

    room_type = models.CharField(max_length=10, choices=RoomType.choices, default=RoomType.DIRECT)
    name = models.CharField(max_length=255, null=True, blank=True)
    direct_key = models.CharField(max_length=41, null=True, blank=True, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_rooms",
    )
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_message_at", "-created_at"]

    def __str__(self):
        if self.name:
            return self.name
        return f"Room {self.pk} ({self.room_type})"

    @staticmethod
    def make_direct_key(user_id_1, user_id_2):
        smaller, larger = sorted([user_id_1, user_id_2])
        return f"{smaller}:{larger}"


class ChatRoomMember(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_message = models.ForeignKey(
        "Message",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        unique_together = [("room", "user")]

    def __str__(self):
        return f"{self.user} in {self.room}"


class Message(models.Model):
    class MessageType(models.TextChoices):
        TEXT = "text", "Text"

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    message_type = models.CharField(max_length=10, choices=MessageType.choices, default=MessageType.TEXT)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["room", "created_at"]),
        ]

    def __str__(self):
        return f"Message {self.pk} by {self.sender} in {self.room}"
