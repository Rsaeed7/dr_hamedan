from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging
import uuid

from .models import SupportMessage, SupportChatRoom
from channels.db import database_sync_to_async
from django.utils import timezone


logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle WebSocket connection."""
        logger.info("🔹 Connecting WebSocket...")

        # Extract room_id from URL route
        self.room_id = self.scope["url_route"]["kwargs"].get("room_id")
        if not self.room_id:
            logger.error("❌ No room_id found")
            await self.send(json.dumps({"error": "Room ID is required"}))
            await self.close()
            return

        # Check if the ChatRoom exists
        try:
            self.chat_room = await database_sync_to_async(SupportChatRoom.objects.get)(id=self.room_id)
        except SupportChatRoom.DoesNotExist:
            logger.error(f"❌ ChatRoom with id {self.room_id} does not exist")
            await self.send(json.dumps({"error": "ChatRoom not found"}))
            await self.close()
            return

        # Define room group name
        self.room_group_name = f"chat_{self.room_id}"

        # Assign user or create guest name
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            self.user = None  # Handle guest users
            self.guest_name = f"Guest-{str(uuid.uuid4())[:8]}"  # Generate unique guest name
        else:
            self.guest_name = self.user.name  # Use authenticated user's username

        # Add WebSocket to the group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"✅ Connected to room {self.room_id} as {self.guest_name}")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        logger.info(f"🔹 Disconnecting WebSocket: {close_code}")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Receive a message from WebSocket."""
        logger.info(f"🔹 Message received: {text_data}")
        try:
            text_data_json = json.loads(text_data)
            message_content = text_data_json.get('message', '').strip()

            # Validate message content
            if not message_content or len(message_content) > 1000:
                logger.error("❌ Invalid message content")
                await self.send(json.dumps({"error": "Invalid message content"}))
                return

            # Save message in database
            await self.save_message(message_content)

            # Send message to WebSocket group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'sender': self.guest_name,
                    'sender_is_admin': self.user.is_admin if self.user else False,
                    'timestamp': str(timezone.now()),
                }
            )
        except json.JSONDecodeError:
            logger.error("❌ Invalid JSON data received")
            await self.send(json.dumps({"error": "Invalid JSON data"}))
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            await self.send(json.dumps({"error": "Internal server error"}))

    async def chat_message(self, event):
        """Receive message from WebSocket group and send it to WebSocket."""
        logger.info(f"🔹 Sending message: {event}")
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'sender_is_admin': event['sender_is_admin'],
            'timestamp': event['timestamp'],
        }))

    async def save_message(self, message_content):
        """Save message in the database."""
        try:
            await database_sync_to_async(SupportMessage.objects.create)(
                sender=self.user,  # Will be None for guests
                content=message_content,
                chat_room=self.chat_room
            )
            logger.info(f"✅ Message saved: {message_content}")
        except Exception as e:
            logger.error(f"❌ Error saving message: {e}")
            raise  # Re-raise the exception to handle it in the caller


class SupportWidgetConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        session = self.scope["session"]

        # جلوگیری از اتصال ادمین
        if self.user.is_staff:
            await self.close()
            return

        # فقط کاربران لاگین شده می‌توانند وصل شوند
        if not self.user.is_authenticated:
            await self.close()
            return

        # برای کاربر لاگین شده: گرفتن یا ساختن چت‌روم
        self.chat_room = await database_sync_to_async(self.get_or_create_chat_room_for_user)(self.user)
        self.room_group_name = f"chat_{self.chat_room.id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # پیام خوشامدگویی
        await self.send(text_data=json.dumps({
            'message': "به پشتیبانی آنلاین خوش آمدید. چگونه می‌توانیم کمک کنیم؟",
            'sender': 'سیستم',
            'sender_is_admin': True,
            'timestamp': str(timezone.now()),
            'is_welcome': True
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_content = text_data_json.get('message', '').strip()

            if not message_content or len(message_content) > 1000:
                await self.send(json.dumps({"error": "Invalid message content"}))
                return

            # ذخیره پیام در دیتابیس
            await self.save_message(message_content)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'sender': self.user.get_full_name(),
                    'sender_is_admin': getattr(self.user, 'is_admin', False),
                    'timestamp': str(timezone.now()),
                }
            )
        except Exception:
            await self.send(json.dumps({"error": "Internal server error"}))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'sender_is_admin': event['sender_is_admin'],
            'timestamp': event['timestamp'],
        }))

    @staticmethod
    def get_or_create_chat_room_for_user(user):
        room, _ = SupportChatRoom.objects.get_or_create(
            customer=user,
            defaults={'title': 'پشتیبانی آنلاین', 'admin_id': 1}
        )
        return room

    @database_sync_to_async
    def save_message(self, content):
        SupportMessage.objects.create(
            chat_room=self.chat_room,
            sender=self.user,
            content=content
        )