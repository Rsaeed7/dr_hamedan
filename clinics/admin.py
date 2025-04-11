from django.contrib import admin
from .models import Clinic, ClinicSpecialty, ClinicGallery


class ClinicSpecialtyInline(admin.TabularInline):
    model = ClinicSpecialty
    extra = 1


class ClinicGalleryInline(admin.TabularInline):
    model = ClinicGallery
    extra = 1


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone', 'email', 'admin')
    search_fields = ('name', 'address', 'phone', 'email', 'admin__username')
    inlines = [ClinicSpecialtyInline, ClinicGalleryInline]


@admin.register(ClinicSpecialty)
class ClinicSpecialtyAdmin(admin.ModelAdmin):
    list_display = ('clinic', 'name')
    list_filter = ('clinic',)
    search_fields = ('clinic__name', 'name')


@admin.register(ClinicGallery)
class ClinicGalleryAdmin(admin.ModelAdmin):
    list_display = ('clinic', 'title')
    list_filter = ('clinic',)
    search_fields = ('clinic__name', 'title')
