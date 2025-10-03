import json
import logging
import base64
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.core.files.base import ContentFile
from .models import ChatRoom, Message

logger = logging.getLogger(__name__)

class MedicalChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"].get("room_id")
        self.user = self.scope.get("user")
        print(f"🔹 Attempting WebSocket connection for room: {self.room_id}")
        print(f"🔹 User: {self.user}")
        print(f"🔹 Channel layer: {self.channel_layer}")

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4003)
            return

        if not self.room_id:
            await self.close(code=4001)
            return

        try:
            self.chat_room = await self.get_chat_room()
        except ChatRoom.DoesNotExist:
            await self.close(code=4004)
            return

        has_access = await self.check_access_permission()
        if not has_access:
            await self.close(code=4003)
            return

        self.room_group_name = f"medical_chat_{self.room_id}"
        self.sender_name = await self.get_sender_name()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"✅ WebSocket connection successful for room: {self.room_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('message_type', 'text')
        message_content = data.get('message', '').strip()
        file_url = data.get('file_url')

        # Validate message for text type
        if message_type == 'text' and (not message_content or len(message_content) > 2000):
            return

        await self.save_message(
            content=message_content,
            message_type=message_type,
            file_url=file_url
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'sender': self.sender_name,
                'sender_id': self.user.id,
                'timestamp': timezone.now().isoformat(),
                'message_type': message_type,
                'file_url': file_url,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp'],
            'message_type': event['message_type'],
            'file_url': event.get('file_url'),
        }))

    @database_sync_to_async
    def get_chat_room(self):
        return ChatRoom.objects.get(id=self.room_id)

    @database_sync_to_async
    def check_access_permission(self):
        try:
            if hasattr(self.user, 'doctor'):
                return self.chat_room.request.doctor == self.user.doctor
            if hasattr(self.user, 'patient'):
                return self.chat_room.request.patient == self.user.patient
        except:
            return False

    @database_sync_to_async
    def get_sender_name(self):
        if hasattr(self.user, 'doctor'):
            return f"دکتر {self.user.get_full_name()}"
        if hasattr(self.user, 'patient'):
            return self.user.get_full_name()
        return "کاربر"

    @database_sync_to_async
    def save_message(self, content, message_type, file_url=None):
        message = Message(
            chat_room=self.chat_room,
            sender=self.user,
            content=content if message_type == 'text' else '',
            message_type=message_type
        )
        if file_url:
            file_path = file_url.replace('/media/', '')
            if message_type == 'audio':
                message.audio.name = file_path
            else:
                message.file.name = file_path
        message.save()
        self.chat_room.last_activity = timezone.now()
        self.chat_room.save()
