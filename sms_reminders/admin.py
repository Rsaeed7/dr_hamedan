from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models
from django.forms import Textarea
from .models import SMSReminder, SMSReminderTemplate, SMSReminderSettings, SMSLog


@admin.register(SMSReminder)
class SMSReminderAdmin(admin.ModelAdmin):
    list_display = (
        'get_patient_name', 'get_doctor_name', 'reminder_type', 
        'phone_number', 'status', 'attempts', 'scheduled_time', 
        'sent_time', 'created_at'
    )
    list_filter = (
        'reminder_type', 'status', 'attempts', 'scheduled_time', 
        'created_at', 'reservation__doctor'
    )
    search_fields = (
        'phone_number', 'reservation__patient__name', 
        'reservation__doctor__user__first_name', 
        'reservation__doctor__user__last_name'
    )
    readonly_fields = (
        'sent_time', 'created_at', 'updated_at', 'sms_response'
    )
    raw_id_fields = ('reservation', 'user')
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('reservation', 'user', 'reminder_type', 'phone_number')
        }),
        ('پیام', {
            'fields': ('message',),
            'classes': ('wide',)
        }),
        ('زمان‌بندی', {
            'fields': ('scheduled_time', 'sent_time')
        }),
        ('وضعیت و تلاش‌ها', {
            'fields': ('status', 'attempts', 'max_attempts')
        }),
        ('پاسخ و خطاها', {
            'fields': ('sms_response', 'error_message'),
            'classes': ('collapse',)
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80})},
    }
    
    def get_patient_name(self, obj):
        if obj.reservation and obj.reservation.patient:
            return obj.reservation.patient.name
        return "میهمان"
    get_patient_name.short_description = 'نام بیمار'
    
    def get_doctor_name(self, obj):
        if obj.reservation and obj.reservation.doctor:
            return obj.reservation.doctor.user.get_full_name()
        return "-"
    get_doctor_name.short_description = 'نام پزشک'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'reservation__patient', 'reservation__doctor__user', 'user'
        )
    
    actions = ['retry_failed_reminders', 'cancel_pending_reminders']
    
    def retry_failed_reminders(self, request, queryset):
        """Retry failed reminders"""
        count = 0
        for reminder in queryset.filter(status='failed'):
            if reminder.can_retry():
                reminder.retry()
                count += 1
        
        self.message_user(
            request, 
            f'{count} یادآوری برای تلاش مجدد آماده شد.'
        )
    retry_failed_reminders.short_description = 'تلاش مجدد یادآوری‌های ناموفق'
    
    def cancel_pending_reminders(self, request, queryset):
        """Cancel pending reminders"""
        updated = queryset.filter(status='pending').update(status='cancelled')
        self.message_user(
            request, 
            f'{updated} یادآوری لغو شد.'
        )
    cancel_pending_reminders.short_description = 'لغو یادآوری‌های در انتظار'


@admin.register(SMSReminderTemplate)
class SMSReminderTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'reminder_type', 'is_active', 'created_at', 'updated_at'
    )
    list_filter = ('reminder_type', 'is_active', 'created_at')
    search_fields = ('name', 'template')
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'reminder_type', 'is_active')
        }),
        ('قالب پیام', {
            'fields': ('template',),
            'description': 'متغیرهای قابل استفاده: {patient_name}, {doctor_name}, {appointment_date}, {appointment_time}, {clinic_name}, {clinic_address}'
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 8, 'cols': 80})},
    }
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['template'].help_text = mark_safe("""
        <strong>متغیرهای قابل استفاده:</strong><br>
        • <code>{patient_name}</code> - نام بیمار<br>
        • <code>{doctor_name}</code> - نام پزشک<br>
        • <code>{appointment_date}</code> - تاریخ نوبت<br>
        • <code>{appointment_time}</code> - ساعت نوبت<br>
        • <code>{clinic_name}</code> - نام کلینیک<br>
        • <code>{clinic_address}</code> - آدرس کلینیک
        """)
        return form


@admin.register(SMSReminderSettings)
class SMSReminderSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'reminder_24h_enabled', 'reminder_2h_enabled', 
        'confirmation_sms_enabled', 'cancellation_sms_enabled',
        'working_hour_start', 'working_hour_end', 'updated_at'
    )
    
    fieldsets = (
        ('تنظیمات کلی', {
            'fields': (
                'reminder_24h_enabled', 'reminder_2h_enabled',
                'confirmation_sms_enabled', 'cancellation_sms_enabled'
            )
        }),
        ('ساعات کاری', {
            'fields': ('working_hour_start', 'working_hour_end'),
            'description': 'پیامک‌ها فقط در این بازه زمانی ارسال می‌شوند'
        }),
        ('تنظیمات پیشرفته', {
            'fields': ('max_retry_attempts', 'retry_interval_minutes')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not SMSReminderSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = (
        'phone_number', 'get_reminder_type', 'success', 
        'get_truncated_message', 'created_at'
    )
    list_filter = ('success', 'created_at', 'reminder__reminder_type')
    search_fields = ('phone_number', 'message', 'error_message')
    readonly_fields = (
        'phone_number', 'message', 'reminder', 'success', 
        'response_data', 'error_message', 'created_at'
    )
    
    fieldsets = (
        ('اطلاعات پیام', {
            'fields': ('phone_number', 'message', 'reminder')
        }),
        ('نتیجه ارسال', {
            'fields': ('success', 'response_data', 'error_message')
        }),
        ('زمان', {
            'fields': ('created_at',)
        })
    )
    
    def get_reminder_type(self, obj):
        if obj.reminder:
            return obj.reminder.get_reminder_type_display()
        return "-"
    get_reminder_type.short_description = 'نوع یادآوری'
    
    def get_truncated_message(self, obj):
        if len(obj.message) > 50:
            return obj.message[:50] + "..."
        return obj.message
    get_truncated_message.short_description = 'متن پیام'
    
    def has_add_permission(self, request):
        # Logs are created automatically
        return False
    
    def has_change_permission(self, request, obj=None):
        # Logs should not be modified
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Allow deletion for cleanup
        return request.user.is_superuser


# Customize admin site header
admin.site.site_header = 'مدیریت سیستم یادآوری پیامکی دکتر ترن'
admin.site.site_title = 'مدیریت یادآوری پیامکی'
admin.site.index_title = 'پنل مدیریت یادآوری پیامکی'
