from django.contrib import admin
from .models import Doctor, DoctorAvailability, Specialization,City,DrServices,DrComment,CommentTips,Email,Supplementary_insurance,DoctorRegistration,EmailTemplate, DoctorBlockedDay

admin.site.register(Email)
admin.site.register(City)
admin.site.register(EmailTemplate)
admin.site.register(Supplementary_insurance)

@admin.register(DoctorRegistration)
class DoctorRegistrationAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'email', 'specialization', 'city', 'status', 'created_at')
    list_filter = ('status', 'specialization', 'city', 'gender', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'national_id', 'license_number')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)
    actions = ['approve_registration', 'reject_registration']
    
    fieldsets = (
        ('اطلاعات شخصی', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'national_id', 'gender')
        }),
        ('اطلاعات حرفه‌ای', {
            'fields': ('specialization', 'license_number', 'city', 'bio', 'consultation_fee', 'consultation_duration')
        }),
        ('مدارک', {
            'fields': ('profile_image', 'license_image', 'degree_image')
        }),
        ('وضعیت درخواست', {
            'fields': ('status',)
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'نام کامل'
    
    @admin.action(description="تایید درخواست‌های انتخاب‌شده")
    def approve_registration(self, request, queryset):
        approved_count = 0
        for registration in queryset.filter(status='pending'):
            registration.approve()
            approved_count += 1
        self.message_user(request, f"{approved_count} درخواست تایید شد.")
    
    @admin.action(description="رد درخواست‌های انتخاب‌شده")
    def reject_registration(self, request, queryset):
        rejected_count = 0
        for registration in queryset.filter(status='pending'):
            registration.reject("رد شده توسط مدیر")
            rejected_count += 1
        self.message_user(request, f"{rejected_count} درخواست رد شد.")

@admin.register(DrComment)
class DrCommentAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'status', 'date','text')
    list_filter = ('status', 'recommendation', 'waiting_time')
    list_editable = ('status',)
    search_fields = ('doctor__name', 'user__username', 'text')
    actions = ['confirm_comments']

    @admin.action(description="تایید کامنت‌های انتخاب‌شده")
    def confirm_comments(self, request, queryset):
        queryset.update(status='confirmed')


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
    list_display = ('__str__', 'specialization', 'city', 'consultation_fee', 'is_available', 'has_location','online_visit')
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
        ('تنظیمات ویزیت آنلاین', {
            'fields': ('online_visit', 'online_visit_fee')
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

@admin.register(DoctorBlockedDay)
class DoctorBlockedDayAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'reason', 'created_at')
    list_filter = ('doctor', 'date', 'created_at')
    search_fields = ('doctor__user__username', 'doctor__user__first_name', 'doctor__user__last_name', 'reason')
    date_hierarchy = 'date'
    ordering = ['-date']
