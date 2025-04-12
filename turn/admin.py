from django.contrib import admin
from . import models
from django_jalali.admin.filters import JDateFieldListFilter

# نمایش اطلاعات بیمار
@admin.register(models.Patients_File)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'meli_code', 'phone')
    search_fields = ("name", "meli_code", "phone")

# مدل Inline برای نوبت‌ها
class InlineReservation(admin.StackedInline):
    model = models.Reservation
    fields = ('get_patient_name', 'doctor', 'phone', 'time', 'status', 'payment_status')
    readonly_fields = ('get_patient_name',)

    def get_patient_name(self, obj):
        # بررسی می‌کنیم که آیا بیمار وجود داره یا نه
        return obj.patient.name if obj.patient else 'بدون بیمار'
    get_patient_name.short_description = 'نام بیمار'

# نمایش اطلاعات نوبت‌ها و بهینه‌سازی کوئری‌ها
@admin.register(models.Reservation_Day)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('date', 'published',)
    list_editable = ('published',)
    list_filter = (('date', JDateFieldListFilter),)
    inlines = (InlineReservation,)
    list_per_page = 100  # فقط 20 نوبت در هر صفحه

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('reservations__patient', 'reservations__doctor')  # لود کردن سریع بیماران و نوبت‌ها

    # نمایش نام بیماران در لیست نوبت‌ها
    def get_patient_names(self, obj):
        patients = obj.reservations.all()
        if patients:
            # بررسی اینکه بیمار وجود داره و سپس اسم‌ش رو نمایش می‌دهیم
            return ', '.join([reservation.patient.name if reservation.patient else 'بدون بیمار' for reservation in patients])
        else:
            return 'بدون بیمار'
    get_patient_names.short_description = 'نام بیماران'

@admin.register(models.Reservation)
class ReservationAdmin(admin.ModelAdmin):
    raw_id_fields = ('patient', 'doctor')
    list_display = ('patient', 'doctor', 'day', 'time', 'status', 'payment_status', 'amount')
    search_fields = ('patient__name', 'patient__meli_code', 'patient__phone', 'doctor__user__first_name', 'doctor__user__last_name')
    list_filter = ('day', 'status', 'payment_status', 'doctor')
    list_per_page = 25
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('اطلاعات نوبت', {
            'fields': ('day', 'time', 'patient', 'doctor', 'phone', 'notes')
        }),
        ('وضعیت', {
            'fields': ('status', 'payment_status', 'amount', 'transaction')
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_confirmed', 'mark_as_completed', 'mark_as_cancelled']
    
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status=models.Reservation.STATUS_CONFIRMED)
        self.message_user(request, f'{updated} نوبت تایید شد.')
    mark_as_confirmed.short_description = "تایید نوبت های انتخاب شده"
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status=models.Reservation.STATUS_COMPLETED)
        self.message_user(request, f'{updated} نوبت تکمیل شد.')
    mark_as_completed.short_description = "تکمیل نوبت های انتخاب شده"
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status=models.Reservation.STATUS_CANCELLED)
        self.message_user(request, f'{updated} نوبت لغو شد.')
    mark_as_cancelled.short_description = "لغو نوبت های انتخاب شده"