from django.urls import path

from chats.views import (
    ChatRoomListView,
    DirectRoomCreateView,
    MarkRoomReadView,
    MessageHistoryView,
)

urlpatterns = [
    path("rooms/direct/", DirectRoomCreateView.as_view(), name="direct_room_create"),
    path("rooms/", ChatRoomListView.as_view(), name="room_list"),
    path("rooms/<int:room_id>/messages/", MessageHistoryView.as_view(), name="message_history"),
    path("rooms/<int:room_id>/read/", MarkRoomReadView.as_view(), name="mark_room_read"),
]
