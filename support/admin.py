from django.contrib import admin
from .models import Contact,ContactUs,SupportMessage,Announcement,SupportChatRoom,AdminChatStatus
admin.site.register(Contact)
admin.site.register(ContactUs)
# admin.site.register(Message)

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("message", "published")
    list_editable = ('published',)

# Register your models here.

@admin.register(SupportChatRoom)
class SupportChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'display_customer', 'display_admin', 'title', 'is_active', 'created_at', 'last_activity')
    list_filter = ('is_active', 'created_at', 'last_activity')
    search_fields = ('admin__name', 'title')
    ordering = ('-last_activity',)

    def display_customer(self, obj):
        return obj.customer.name if obj.customer else "Guest"

    display_customer.short_description = "Customer"

    def display_admin(self, obj):
        return obj.admin.name if obj.admin else "Not Assigned"

    display_admin.short_description = "Admin"


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat_room', 'display_sender', 'content', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('chat_room__id', 'content')
    ordering = ('created_at',)

    def display_sender(self, obj):
        return obj.sender.name if obj.sender else "Anonymous"

    display_sender.short_description = "Sender"


@admin.register(AdminChatStatus)
class AdminChatStatusAdmin(admin.ModelAdmin):
    list_display = ('admin', 'is_available', 'last_active')
    list_filter = ('is_available', 'last_active')
    search_fields = ('admin__username',)
