from django.urls import re_path
from .consumers import MedicalChatConsumer

websocket_urlpatterns = [
    re_path(
        r'ws/medical-chat/(?P<room_id>\d+)/$',
        MedicalChatConsumer.as_asgi(),
        name='medical_chat_ws'
    ),
]