from django.db import models
from django_jalali.db import models as jmodels
from django.utils.translation import gettext_lazy as _
from reservations.models import Reservation
from user.models import User


class SMSReminder(models.Model):
    """
    Model to track SMS reminders sent to patients
    """
    REMINDER_TYPES = (
        ('confirmation', 'تایید نوبت'),
        ('reminder_24h', 'یادآوری ۲۴ ساعته'),
        ('reminder_2h', 'یادآوری ۲ ساعته'),
        ('cancellation', 'لغو نوبت'),
        ('custom', 'پیام سفارشی'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'در انتظار ارسال'),
        ('sent', 'ارسال شده'),
        ('failed', 'ناموفق'),
        ('cancelled', 'لغو شده'),
    )
    
    reservation = models.ForeignKey(
        Reservation, 
        on_delete=models.CASCADE, 
        related_name='sms_reminders',
        verbose_name=_('رزرو')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sms_reminders',
        verbose_name=_('کاربر')
    )
    
    reminder_type = models.CharField(
        max_length=20, 
        choices=REMINDER_TYPES, 
        verbose_name=_('نوع یادآوری')
    )
    phone_number = models.CharField(
        max_length=20, 
        verbose_name=_('شماره تلفن')
    )
    message = models.TextField(verbose_name=_('متن پیام'))
    
    # Scheduling
    scheduled_time = jmodels.jDateTimeField(
        verbose_name=_('زمان برنامه‌ریزی شده')
    )
    sent_time = jmodels.jDateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_('زمان ارسال')
    )
    
    # Status and tracking
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name=_('وضعیت')
    )
    attempts = models.PositiveIntegerField(
        default=0, 
        verbose_name=_('تعداد تلاش')
    )
    max_attempts = models.PositiveIntegerField(
        default=3, 
        verbose_name=_('حداکثر تلاش')
    )
    
    # Response from SMS service
    sms_response = models.JSONField(
        null=True, 
        blank=True, 
        verbose_name=_('پاسخ سرویس پیامک')
    )
    error_message = models.TextField(
        null=True, 
        blank=True, 
        verbose_name=_('پیام خطا')
    )
    
    # Metadata
    created_at = jmodels.jDateTimeField(
        auto_now_add=True, 
        verbose_name=_('تاریخ ایجاد')
    )
    updated_at = jmodels.jDateTimeField(
        auto_now=True, 
        verbose_name=_('تاریخ بروزرسانی')
    )
    
    class Meta:
        verbose_name = _('یادآوری پیامکی')
        verbose_name_plural = _('یادآوری‌های پیامکی')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['scheduled_time', 'status']),
            models.Index(fields=['reservation', 'reminder_type']),
            models.Index(fields=['status', 'attempts']),
        ]
    
    def __str__(self):
        patient_name = self.reservation.patient.name if self.reservation.patient else "Guest"
        return f"{patient_name} - {self.get_reminder_type_display()} - {self.status}"
    
    def can_retry(self):
        """Check if this reminder can be retried"""
        return (
            self.status == 'failed' and 
            self.attempts < self.max_attempts
        )
    
    def mark_as_sent(self, response_data=None):
        """Mark reminder as successfully sent"""
        from django.utils import timezone
        import json
        
        self.status = 'sent'
        self.sent_time = timezone.now()
        if response_data:
            # Ensure response_data is JSON serializable
            try:
                # Try to serialize to test if it's valid JSON
                json.dumps(response_data)
                self.sms_response = response_data
            except (TypeError, ValueError):
                # If not serializable, convert to string
                self.sms_response = {'response': str(response_data)}
        self.save()
    
    def mark_as_failed(self, error_message):
        """Mark reminder as failed with error message"""
        self.status = 'failed'
        self.attempts += 1
        self.error_message = error_message
        self.save()
    
    def retry(self):
        """Reset for retry"""
        if self.can_retry():
            self.status = 'pending'
            self.error_message = None
            self.save()
            return True
        return False


class SMSReminderTemplate(models.Model):
    """
    Template for SMS reminder messages
    """
    name = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name=_('نام قالب')
    )
    reminder_type = models.CharField(
        max_length=20, 
        choices=SMSReminder.REMINDER_TYPES,
        verbose_name=_('نوع یادآوری')
    )
    template = models.TextField(
        verbose_name=_('قالب پیام'),
        help_text=_('از متغیرهای زیر استفاده کنید: {patient_name}, {doctor_name}, {appointment_date}, {appointment_time}, {clinic_name}, {clinic_address}')
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name=_('فعال')
    )
    
    created_at = jmodels.jDateTimeField(
        auto_now_add=True, 
        verbose_name=_('تاریخ ایجاد')
    )
    updated_at = jmodels.jDateTimeField(
        auto_now=True, 
        verbose_name=_('تاریخ بروزرسانی')
    )
    
    class Meta:
        verbose_name = _('قالب یادآوری پیامکی')
        verbose_name_plural = _('قالب‌های یادآوری پیامکی')
        unique_together = ['name', 'reminder_type']
    
    def __str__(self):
        return f"{self.name} - {self.get_reminder_type_display()}"
    
    def render_message(self, reservation):
        """
        Render the template with reservation data
        """
        patient_name = reservation.patient.name if reservation.patient else "عزیز"
        doctor_name = reservation.doctor.user.get_full_name()
        appointment_date = reservation.day.date.strftime('%Y/%m/%d')
        appointment_time = reservation.time.strftime('%H:%M')
        clinic_name = reservation.doctor.clinic.name if reservation.doctor.clinic else "کلینیک"
        clinic_address = reservation.doctor.clinic.address if reservation.doctor.clinic else ""
        
        context = {
            'patient_name': patient_name,
            'doctor_name': doctor_name,
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'clinic_name': clinic_name,
            'clinic_address': clinic_address,
        }
        
        return self.template.format(**context)


class SMSReminderSettings(models.Model):
    """
    Settings for SMS reminder system
    """
    reminder_24h_enabled = models.BooleanField(
        default=True, 
        verbose_name=_('یادآوری ۲۴ ساعته فعال')
    )
    reminder_2h_enabled = models.BooleanField(
        default=True, 
        verbose_name=_('یادآوری ۲ ساعته فعال')
    )
    confirmation_sms_enabled = models.BooleanField(
        default=True, 
        verbose_name=_('پیامک تایید فعال')
    )
    cancellation_sms_enabled = models.BooleanField(
        default=True, 
        verbose_name=_('پیامک لغو فعال')
    )
    
    # Working hours for sending reminders
    working_hour_start = models.TimeField(
        default='08:00', 
        verbose_name=_('شروع ساعات کاری')
    )
    working_hour_end = models.TimeField(
        default='20:00', 
        verbose_name=_('پایان ساعات کاری')
    )
    
    # Advanced settings
    max_retry_attempts = models.PositiveIntegerField(
        default=3, 
        verbose_name=_('حداکثر تلاش مجدد')
    )
    retry_interval_minutes = models.PositiveIntegerField(
        default=30, 
        verbose_name=_('فاصله تلاش مجدد (دقیقه)')
    )
    
    created_at = jmodels.jDateTimeField(
        auto_now_add=True, 
        verbose_name=_('تاریخ ایجاد')
    )
    updated_at = jmodels.jDateTimeField(
        auto_now=True, 
        verbose_name=_('تاریخ بروزرسانی')
    )
    
    class Meta:
        verbose_name = _('تنظیمات یادآوری پیامکی')
        verbose_name_plural = _('تنظیمات یادآوری پیامکی')
    
    def __str__(self):
        return f"تنظیمات یادآوری پیامکی - {self.updated_at.strftime('%Y/%m/%d')}"
    
    @classmethod
    def get_settings(cls):
        """Get or create settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class SMSLog(models.Model):
    """
    Log of all SMS activities for auditing and debugging
    """
    phone_number = models.CharField(
        max_length=20, 
        verbose_name=_('شماره تلفن')
    )
    message = models.TextField(verbose_name=_('متن پیام'))
    reminder = models.ForeignKey(
        SMSReminder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        verbose_name=_('یادآوری')
    )
    
    # Response data
    success = models.BooleanField(verbose_name=_('موفق'))
    response_data = models.JSONField(
        null=True, 
        blank=True, 
        verbose_name=_('داده‌های پاسخ')
    )
    error_message = models.TextField(
        null=True, 
        blank=True, 
        verbose_name=_('پیام خطا')
    )
    
    # Timing
    created_at = jmodels.jDateTimeField(
        auto_now_add=True, 
        verbose_name=_('زمان ارسال')
    )
    
    class Meta:
        verbose_name = _('لاگ پیامک')
        verbose_name_plural = _('لاگ‌های پیامک')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number', 'created_at']),
            models.Index(fields=['success', 'created_at']),
        ]
    
    def __str__(self):
        status = "موفق" if self.success else "ناموفق"
        return f"{self.phone_number} - {status} - {self.created_at.strftime('%Y/%m/%d %H:%M')}"
