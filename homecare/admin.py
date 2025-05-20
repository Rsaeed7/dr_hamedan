import os

from django.contrib import admin
from django.utils.html import format_html

from .models import ServiceCategory, Service, HomeCareRequest

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'estimated_price', 'requires_prescription']
    list_filter = ['category', 'requires_prescription']
    search_fields = ['name', 'description']

@admin.register(HomeCareRequest)
class HomeCareRequestAdmin(admin.ModelAdmin):
    ...
    readonly_fields = ['created_at', 'prescription_preview']

    fieldsets = (
        (None, {
            'fields': (
                'patient', 'service', 'requested_date', 'requested_time',
                'address', 'extra_notes', 'prescription_file', 'prescription_preview', 'status'
            )
        }),
        ('سیستمی', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    def prescription_preview(self, obj):
        if obj.prescription_file:
            ext = os.path.splitext(obj.prescription_file.name)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                return format_html('<img src="{}" style="max-height: 100px;" />', obj.prescription_file.url)
            else:
                return format_html('<a href="{}" target="_blank">دانلود نسخه</a>', obj.prescription_file.url)
        return "ندارد"

    prescription_preview.short_description = "نسخه آپلودشده"
