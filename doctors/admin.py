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
    list_display = ('__str__', 'specialization', 'city', 'consultation_fee', 'is_available', 'has_location')
    list_filter = ('is_available', 'is_independent', 'specialization', 'city')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialization__name')
    inlines = [DoctorServicesInline, ]
    
    fieldsets = (
        ('اطلاعات کاربری', {
            'fields': ('user', 'specialization', 'license_number', 'gender')
        }),
        ('اطلاعات تماس و مکان', {
            'fields': ('city', 'address', 'phone', 'latitude', 'longitude'),
            'description': 'برای تعین موقعیت جغرافیایی، عرض و طول جغرافیایی را وارد کنید'
        }),
        ('اطلاعات پروفایل', {
            'fields': ('profile_image', 'bio', 'clinic', 'Insurance')
        }),
        ('تنظیمات ویزیت', {
            'fields': ('consultation_fee', 'consultation_duration', 'is_available', 'is_independent')
        }),
    )
    
    def has_location(self, obj):
        """Check if doctor has location coordinates"""
        return bool(obj.latitude and obj.longitude)
    has_location.boolean = True
    has_location.short_description = 'موقعیت جغرافیایی'

@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'get_day_of_week_display', 'start_time', 'end_time')
    list_filter = ('day_of_week', 'doctor')
    search_fields = ('doctor__user__username', 'doctor__user__first_name', 'doctor__user__last_name')
