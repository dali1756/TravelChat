from django.urls import re_path

from chats.consumers import AIConsumer, ChatConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_id>\d+)/$", ChatConsumer.as_asgi()),
    re_path(r"ws/ai/(?P<conversation_id>\d+)/$", AIConsumer.as_asgi()),
]
