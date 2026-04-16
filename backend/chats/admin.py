from django.contrib import admin

from chats.models import ChatRoom, ChatRoomMember, Message


class ChatRoomMemberInline(admin.TabularInline):
    model = ChatRoomMember
    extra = 0
    readonly_fields = ("joined_at",)


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "room_type", "name", "direct_key", "created_by", "last_message_at", "created_at")
    list_filter = ("room_type",)
    search_fields = ("name", "direct_key")
    readonly_fields = ("created_at", "updated_at")
    inlines = [ChatRoomMemberInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "sender", "message_type", "created_at")
    list_filter = ("message_type",)
    search_fields = ("content",)
    readonly_fields = ("created_at",)
