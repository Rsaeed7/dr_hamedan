from django.db import models
from django.utils import timezone
from doctors.models import Doctor
from patients.models import PatientsFile as Patient
from user.models import User


class ChatRequest(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

    STATUS_CHOICES = [
        (PENDING, 'در انتظار تایید'),
        (APPROVED, 'تایید شده'),
        (REJECTED, 'رد شده'),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='chat_requests',
        verbose_name='بیمار'
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='chat_requests',
        verbose_name='پزشک'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        verbose_name='وضعیت'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        unique_together = ('patient', 'doctor')
        ordering = ['-created_at']
        verbose_name = 'درخواست چت'
        verbose_name_plural = 'درخواست‌های چت'

    def __str__(self):
        return f"درخواست چت {self.id} - بیمار: {self.patient.user.name}"


class ChatRoom(models.Model):
    request = models.OneToOneField(
        ChatRequest,
        on_delete=models.CASCADE,
        related_name='chat_room',
        verbose_name='درخواست مربوطه'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name='آخرین فعالیت'
    )

    class Meta:
        ordering = ['-last_activity']
        verbose_name = 'اتاق چت'
        verbose_name_plural = 'اتاق‌های چت'

    def __str__(self):
        return f"اتاق چت {self.id} - پزشک: {self.request.doctor.user.name}"


class Message(models.Model):
    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='اتاق چت'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='فرستنده'
    )
    content = models.TextField(verbose_name='محتوا')

    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='تاریخ ارسال'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='خوانده شده'
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = 'پیام'
        verbose_name_plural = 'پیام‌ها'



    def __str__(self):
        return f"پیام {self.id} - {self.sender.name if self.sender else 'ناشناس'}"


class DoctorAvailability(models.Model):
    doctor = models.OneToOneField(
        Doctor,
        on_delete=models.CASCADE,
        related_name='availability',
        verbose_name='پزشک'
    )
    is_available = models.BooleanField(
        default=False,
        verbose_name='وضعیت دسترسی'
    )
    last_active = models.DateTimeField(
        auto_now=True,
        verbose_name='آخرین فعالیت'
    )

    class Meta:
        verbose_name = 'وضعیت دسترسی پزشک'
        verbose_name_plural = 'وضعیت دسترسی پزشکان'

    def __str__(self):
        return f"{self.doctor.user.name} - {'آنلاین' if self.is_available else 'آفلاین'}"