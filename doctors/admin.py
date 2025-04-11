from django.contrib import admin
from .models import Doctor, DoctorAvailability


class DoctorAvailabilityInline(admin.TabularInline):
    model = DoctorAvailability
    extra = 1


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'consultation_fee', 'is_independent', 'is_available')
    list_filter = ('specialization', 'is_independent', 'is_available')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialization')
    inlines = [DoctorAvailabilityInline]


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day_of_week', 'start_time', 'end_time')
    list_filter = ('day_of_week', 'doctor')
    search_fields = ('doctor__user__username', 'doctor__user__first_name', 'doctor__user__last_name')
