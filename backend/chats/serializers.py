from rest_framework import serializers

from chats.models import ChatRoom, Message
from members.models import User


class PeerSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class DirectRoomCreateSerializer(serializers.Serializer):
    peer_user_id = serializers.IntegerField()

    def validate_peer_user_id(self, value):
        request_user = self.context["request"].user
        if value == request_user.id:
            raise serializers.ValidationError("不能與自己建立聊天室。")
        if not User.objects.public().filter(id=value).exists():
            raise serializers.ValidationError("找不到該使用者。")
        return value


class LastMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "content", "sender_username", "created_at"]


class ChatRoomListSerializer(serializers.ModelSerializer):
    peer = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ["id", "room_type", "peer", "last_message", "last_message_at", "created_at"]

    def get_peer(self, obj):
        request_user = self.context["request"].user
        peer_member = obj.members.exclude(user=request_user).select_related("user").first()
        if peer_member:
            return PeerSummarySerializer(peer_member.user).data
        return None

    def get_last_message(self, obj):
        msg = obj.messages.select_related("sender").order_by("-created_at").first()
        if msg:
            return LastMessageSerializer(msg).data
        return None


class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(source="sender.id", read_only=True)
    sender_username = serializers.CharField(source="sender.username", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "sender_id", "sender_username", "message_type", "content", "created_at"]
