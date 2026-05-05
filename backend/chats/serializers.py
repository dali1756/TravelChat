from rest_framework import serializers

from chats.models import ChatRoom, ChatRoomMember, Message
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
    unread_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = ChatRoom
        fields = ["id", "room_type", "name", "peer", "last_message", "last_message_at", "created_at", "unread_count"]

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


class MarkRoomReadSerializer(serializers.Serializer):
    message_id = serializers.IntegerField(required=False, allow_null=True)


class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(source="sender.id", read_only=True)
    sender_username = serializers.CharField(source="sender.username", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "sender_id", "sender_username", "message_type", "content", "created_at"]


class GroupRoomCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    member_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)

    def validate_member_ids(self, value):
        if not value:
            return value
        existing_ids = set(User.objects.public().filter(id__in=value).values_list("id", flat=True))
        missing = set(value) - existing_ids
        if missing:
            raise serializers.ValidationError(f"找不到使用者：{sorted(missing)}")
        return value


class RoomMemberUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class RoomMemberSerializer(serializers.ModelSerializer):
    user = RoomMemberUserSerializer(read_only=True)

    class Meta:
        model = ChatRoomMember
        fields = ["id", "user", "joined_at"]


class RoomMemberAddSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

    def validate_user_id(self, value):
        if not User.objects.public().filter(id=value).exists():
            raise serializers.ValidationError("找不到該使用者。")
        return value
