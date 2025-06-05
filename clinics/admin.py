from django.contrib import admin
from .models import Clinic, ClinicSpecialty, ClinicGallery,ClinicComment

@admin.register(ClinicComment)
class ClinicCommentAdmin(admin.ModelAdmin):
    list_display = ('clinic', 'status', 'date','text')
    list_filter = ('status', 'recommendation',)
    list_editable = ('status',)
    actions = ['confirm_comments']

    @admin.action(description="تایید کامنت‌های انتخاب‌شده")
    def confirm_comments(self, request, queryset):
        queryset.update(status='confirmed')

class ClinicSpecialtyInline(admin.TabularInline):
    model = ClinicSpecialty
    extra = 1

class ClinicGalleryInline(admin.TabularInline):
    model = ClinicGallery
    extra = 1

@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ('name', 'admin', 'phone', 'email')
    search_fields = ('name', 'address', 'admin__username')
    inlines = [ClinicSpecialtyInline, ClinicGalleryInline]

@admin.register(ClinicSpecialty)
class ClinicSpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'clinic')
    list_filter = ('clinic',)
    search_fields = ('name', 'clinic__name')

@admin.register(ClinicGallery)
class ClinicGalleryAdmin(admin.ModelAdmin):
    list_display = ('clinic', 'title', 'created_at')
    list_filter = ('clinic', 'created_at')
    search_fields = ('clinic__name', 'title')
