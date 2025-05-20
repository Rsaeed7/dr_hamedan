from django.contrib import admin
from .models import Doctor, DoctorAvailability, Specialization,City,DrServices,DrComment,CommentTips,Email,Supplementary_insurance

admin.site.register(Email)
admin.site.register(City)
admin.site.register(Supplementary_insurance)

admin.site.register(DrComment)
admin.site.register(CommentTips)
class DoctorServicesInline(admin.TabularInline):
    model = DrServices
    extra = 1

@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'specialization', 'consultation_fee', 'is_available')
    list_filter = ('is_available', 'is_independent', 'specialization')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialization')
    inlines = [DoctorServicesInline, ]

@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'get_day_of_week_display', 'start_time', 'end_time')
    list_filter = ('day_of_week', 'doctor')
    search_fields = ('doctor__user__username', 'doctor__user__first_name', 'doctor__user__last_name')
