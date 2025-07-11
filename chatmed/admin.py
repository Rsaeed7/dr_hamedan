from django.contrib import admin
from .models import ChatRoom, Message, ChatRequest, DoctorAvailability
from django.utils.html import format_html


@admin.register(ChatRequest)
class ChatRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient_info', 'doctor_info', 'status', 'payment_status', 'amount', 'created_at', 'updated_at')
    list_filter = ('status', 'payment_status', 'created_at', 'updated_at')
    search_fields = (
        'patient__user__first_name',
        'patient__user__last_name',
        'doctor__user__first_name',
        'doctor__user__last_name',
        'patient_name',
        'phone'
    )
    ordering = ('-created_at',)
    list_editable = ('status',)
    readonly_fields = ('transaction_link', 'created_at', 'updated_at')
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('patient', 'doctor', 'disease_summary', 'status')
        }),
        ('اطلاعات پرداخت', {
            'fields': ('amount', 'payment_status', 'transaction_link')
        }),
        ('اطلاعات بیمار', {
            'fields': ('patient_name', 'patient_national_id', 'phone')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def patient_info(self, obj):
        return format_html(
            '<a href="/admin/patients/patientsfile/{}/change/">{}</a>',
            obj.patient.id,
            obj.patient.user.get_full_name()
        )
    patient_info.short_description = 'Patient'

    def doctor_info(self, obj):
        return format_html(
            '<a href="/admin/doctors/doctor/{}/change/">{}</a>',
            obj.doctor.id,
            f"Dr. {obj.doctor.user.get_full_name()}"
        )
    doctor_info.short_description = 'Doctor'
    
    def transaction_link(self, obj):
        if obj.transaction:
            return format_html(
                '<a href="/admin/wallet/transaction/{}/change/">Transaction #{}</a>',
                obj.transaction.id,
                obj.transaction.id
            )
        return "No Transaction"
    transaction_link.short_description = 'Transaction'
    
    def amount(self, obj):
        return f"{obj.amount:,} تومان"
    amount.short_description = 'Amount'

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'request_link',
        'is_active',
        'last_activity',
        'message_count'
    )
    list_filter = ('is_active', 'last_activity')
    search_fields = (
        'request__patient__user__first_name',
        'request__doctor__user__first_name'
    )
    ordering = ('-last_activity',)

    def request_link(self, obj):
        return format_html(
            '<a href="/admin/chat/chatrequest/{}/change/">Request #{}</a>',
            obj.request.id,
            obj.request.id
        )
    request_link.short_description = 'Chat Request'

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sender_type',
        'short_content',
        'chat_room_link',
        'created_at',
        'is_read'
    )
    list_filter = ('is_read', 'created_at')
    search_fields = ('content', 'chat_room__id')
    list_editable = ('is_read',)
    ordering = ('-created_at',)

    def sender_type(self, obj):
        if obj.sender:
            if hasattr(obj.sender, 'doctor'):
                return "Doctor"
            elif hasattr(obj.sender, 'patient'):
                return "Patient"
        return "System"
    sender_type.short_description = 'Sender Type'

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'

    def chat_room_link(self, obj):
        return format_html(
            '<a href="/admin/chat/chatroom/{}/change/">Room #{}</a>',
            obj.chat_room.id,
            obj.chat_room.id
        )
    chat_room_link.short_description = 'Chat Room'

@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = (
        'doctor_info',
        'is_available',
        'last_active',
        'current_status'
    )
    list_filter = ('is_available',)
    search_fields = (
        'doctor__user__first_name',
        'doctor__user__last_name'
    )

    def doctor_info(self, obj):
        return format_html(
            '<a href="/admin/doctors/doctor/{}/change/">{}</a>',
            obj.doctor.id,
            f"Dr. {obj.doctor.user.get_full_name()}"
        )
    doctor_info.short_description = 'Doctor'

    def current_status(self, obj):
        if obj.is_available:
            return format_html('<span style="color: green;">● Available</span>')
        return format_html('<span style="color: red;">● Offline</span>')
    current_status.short_description = 'Status'