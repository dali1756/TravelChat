from django.urls import path

from chats.views import (
    ChatRoomListView,
    DirectRoomCreateView,
    GroupRoomCreateView,
    MarkRoomReadView,
    MessageHistoryView,
    RoomMemberRemoveView,
    RoomMembersView,
)

urlpatterns = [
    path("rooms/direct/", DirectRoomCreateView.as_view(), name="direct_room_create"),
    path("rooms/group/", GroupRoomCreateView.as_view(), name="group_room_create"),
    path("rooms/", ChatRoomListView.as_view(), name="room_list"),
    path("rooms/<int:room_id>/messages/", MessageHistoryView.as_view(), name="message_history"),
    path("rooms/<int:room_id>/read/", MarkRoomReadView.as_view(), name="mark_room_read"),
    path("rooms/<int:room_id>/members/", RoomMembersView.as_view(), name="room_members"),
    path("rooms/<int:room_id>/members/<int:user_id>/", RoomMemberRemoveView.as_view(), name="room_member_remove"),
]
