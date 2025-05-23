from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import ChatRoom, Message
from doctors.models import Doctor
from patients.models import PatientsFile as Patient

logger = logging.getLogger(__name__)

class MedicalChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"].get("room_id")
        if not self.room_id:
            await self.close(code=4001)
            return

        try:
            self.chat_room = await self.get_chat_room()
            self.user = self.scope["user"]

            if not await self.check_access_permission():
                await self.close(code=4003)
                return

        except ChatRoom.DoesNotExist:
            await self.close(code=4004)
            return

        self.room_group_name = f"medical_chat_{self.room_id}"
        self.sender_name = await self.get_sender_name()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    @database_sync_to_async
    def get_chat_room(self):
        return ChatRoom.objects.select_related('request__doctor__user', 'request__patient__user').get(id=self.room_id)

    @database_sync_to_async
    def check_access_permission(self):
        if not self.user.is_authenticated:
            return False
        if hasattr(self.user, 'doctor'):
            return self.chat_room.request.doctor == self.user.doctor
        if hasattr(self.user, 'patient'):
            return self.chat_room.request.patient == self.user.patient
        return False

    @database_sync_to_async
    def get_sender_name(self):
        if hasattr(self.user, 'doctor'):
            return f"Dr. {self.user.get_full_name()}"
        elif hasattr(self.user, 'patient'):
            return self.user.get_full_name()
        return "Anonymous"

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_content = data.get('message', '').strip()

            if not message_content or len(message_content) > 2000:
                return

            await self.save_message(message_content)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'sender': self.sender_name,
                    'sender_id': self.user.id,
                    'is_doctor': hasattr(self.user, 'doctor'),
                    'timestamp': timezone.now().isoformat(),
                }
            )

        except json.JSONDecodeError:
            logger.error("❌ Invalid JSON data")
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'sender_id': event['sender_id'],  # ✅ اضافه شد
            'is_doctor': event['is_doctor'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def save_message(self, content):
        Message.objects.create(
            chat_room=self.chat_room,
            sender=self.user,
            content=content
        )
        self.chat_room.last_activity = timezone.now()
        self.chat_room.save()
