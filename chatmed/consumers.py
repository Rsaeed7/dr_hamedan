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
        """اتصال WebSocket برای چت پزشکی"""
        logger.info("🔹 Establishing medical WebSocket connection...")

        # دریافت room_id از URL
        self.room_id = self.scope["url_route"]["kwargs"].get("room_id")
        if not self.room_id:
            logger.error("❌ Room ID not provided")
            await self.close(code=4001)
            return

        # بررسی وجود اتاق چت و دسترسی کاربر
        try:
            self.chat_room = await self.get_chat_room()
            self.user = self.scope["user"]

            if not await self.check_access_permission():
                logger.error(f"❌ Access denied for user {self.user}")
                await self.close(code=4003)
                return

        except ChatRoom.DoesNotExist:
            logger.error(f"❌ ChatRoom {self.room_id} not found")
            await self.close(code=4004)
            return

        # تنظیمات گروه
        self.room_group_name = f"medical_chat_{self.room_id}"
        self.sender_name = await self.get_sender_name()

        # اضافه کردن به گروه
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"✅ {self.sender_name} connected to room {self.room_id}")

    @database_sync_to_async
    def get_chat_room(self):
        """دریافت اتاق چت از دیتابیس"""
        return ChatRoom.objects.select_related('request__doctor__user', 'request__patient__user').get(id=self.room_id)

    @database_sync_to_async
    def check_access_permission(self):
        """بررسی مجوز دسترسی کاربر به اتاق چت"""
        if not self.user.is_authenticated:
            return False

        # اگر کاربر پزشک است
        if hasattr(self.user, 'doctor'):
            return self.chat_room.request.doctor == self.user.doctor

        # اگر کاربر بیمار است
        if hasattr(self.user, 'patient'):
            return self.chat_room.request.patient == self.user.patient

        return False

    @database_sync_to_async
    def get_sender_name(self):
        """دریافت نام فرستنده"""
        if hasattr(self.user, 'doctor'):
            return f"Dr. {self.user.get_full_name()}"
        elif hasattr(self.user, 'patient'):
            return self.user.get_full_name()
        return "Anonymous"

    async def disconnect(self, close_code):
        """قطع ارتباط WebSocket"""
        logger.info(f"🔹 Disconnecting from room {self.room_id}, code: {close_code}")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """دریافت پیام از WebSocket"""
        try:
            data = json.loads(text_data)
            message_content = data.get('message', '').strip()

            # اعتبارسنجی پیام
            if not message_content or len(message_content) > 2000:
                logger.warning("⚠️ Invalid message content")
                return

            # ذخیره پیام
            await self.save_message(message_content)

            # ارسال پیام به گروه
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'sender': self.sender_name,
                    'is_doctor': hasattr(self.user, 'doctor'),
                    'timestamp': timezone.now().isoformat(),
                }
            )

        except json.JSONDecodeError:
            logger.error("❌ Invalid JSON data")
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")

    async def chat_message(self, event):
        """ارسال پیام به کلاینت"""
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'is_doctor': event['is_doctor'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def save_message(self, content):
        """ذخیره پیام در دیتابیس"""
        Message.objects.create(
            chat_room=self.chat_room,
            sender=self.user,
            content=content
        )
        # به روزرسانی زمان آخرین فعالیت
        self.chat_room.last_activity = timezone.now()
        self.chat_room.save()