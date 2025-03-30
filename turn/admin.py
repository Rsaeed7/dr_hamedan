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
    fields = ('get_patient_name','phone','time')  # فقط نمایش اسم بیمار و زمان نوبت
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
        return qs.prefetch_related('reservations__patient')  # لود کردن سریع بیماران و نوبت‌ها

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
    raw_id_fields = ('patient',)  # فقط شناسه بیمار نمایش داده می‌شود
    list_display = ('patient', 'day', 'time')
    search_fields = ('patient__name', 'patient__meli_code', 'patient__phone')  # جستجو بر اساس نام، کد ملی و شماره تلفن بیمار
    list_filter = ('day',)  # فیلتر بر اساس تاریخ نوبت
    list_per_page = 25  # فقط 20 نوبت در هر صفحه