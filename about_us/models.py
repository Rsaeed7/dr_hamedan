from django.db import models
from django.utils import timezone

from user.models import User


class SupportChatRoom(models.Model):
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='customer_chats',
        null=True, blank=True,
        help_text="The customer who initiated the chat (null for anonymous)"
    )
    admins = models.ManyToManyField(
        User,
        related_name='admin_chats',
        blank=True,
        help_text="Admins assigned to this chat room"
    )
    title = models.CharField(max_length=200, default="Customer Support Chat")
    is_active = models.BooleanField(default=True, help_text="Indicates if chat room is active")
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(default=timezone.now, help_text="Timestamp of last message")

    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['customer', 'is_active']),
        ]

    def __str__(self):
        return f"ChatRoom {self.id} - {self.title}"



class SupportMessage(models.Model):
    """
    Stores individual messages within a chat room.
    """
    chat_room = models.ForeignKey(
        SupportChatRoom,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        null=True, blank=True,
        help_text="Message sender; null for anonymous"
    )
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chat_room', 'created_at']),
        ]

    def __str__(self):
        return f"Message {self.id} at {self.created_at}"


class AdminChatStatus(models.Model):
    """
    Tracks admin availability for chat support.
    """
    admin = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='chat_status'
    )
    is_available = models.BooleanField(default=False)
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Admin Chat Status"
        verbose_name_plural = "Admin Chat Statuses"

    def __str__(self):
        return f"{self.admin.name} - {'Available' if self.is_available else 'Unavailable'}"




class Contact(models.Model):
    phone_number = models.CharField(max_length=11,verbose_name='شماره تلفن')
    email = models.EmailField(verbose_name='ایمیل')
    address = models.TextField(verbose_name='آدرس')
    whatsapp = models.CharField(max_length=100,verbose_name='واتساپ')
    telegram = models.CharField(max_length=100,verbose_name='تلگرام')
    instagram = models.CharField(max_length=100,verbose_name='اینستاگرام')
    eitaa = models.CharField(max_length=100,verbose_name='ایتا')

    def __str__(self):
        return self.email
    class Meta:
        verbose_name='اطلاعات تماس'
        verbose_name_plural='اطلاعات تماس'


class ContactUs(models.Model):
    name = models.CharField(max_length=50,verbose_name='نام')
    email = models.EmailField(verbose_name='ایمیل')
    subject = models.CharField(max_length=100,verbose_name='موضوع')
    message = models.TextField(verbose_name='پیام')

    def __str__(self):
        return f'{self.name} - {self.subject}'

    class Meta:
        verbose_name='پیام کاربر'
        verbose_name_plural='پیام کاربران'

class Announcement(models.Model):
    message = models.CharField(max_length=65,verbose_name='اعلامیه',blank=True,null=True)
    published = models.BooleanField(default=False,verbose_name='نمایش داده شود',blank=True,null=True)

    def __str__(self):
        return f'{self.message}'
    class Meta:
        verbose_name='اعلامیه'
        verbose_name_plural='اعلامیه ها'

