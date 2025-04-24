from django.db import models
from django.contrib.auth.models import User
from clinics.models import Clinic
from datetime import time, datetime, timedelta
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _



class Specialization(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('نام تخصص'))
    description = models.TextField(blank=True, verbose_name=_('توضیحات'))
    image = models.ImageField(upload_to='specializations/', blank=True, null=True, verbose_name=_('تصویر'))

    class Meta:
        verbose_name = _('تخصص')
        verbose_name_plural = _('تخصص‌ها')
        ordering = ['name']

    def __str__(self):
        return self.name
    

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_('کاربر'))
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True, verbose_name=_('تخصص'))
    license_number = models.CharField(max_length=50, unique=True, verbose_name=_('شماره پروانه'))
    bio = models.TextField(blank=True, verbose_name=_('بیوگرافی'))
    profile_image = models.ImageField(upload_to='doctor_profiles/', blank=True, null=True, verbose_name=_('تصویر پروفایل'))
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_('هزینه مشاوره'))
    consultation_duration = models.IntegerField(default=30, validators=[MinValueValidator(15), MaxValueValidator(120)], verbose_name=_('مدت زمان مشاوره (دقیقه)'))
    is_independent = models.BooleanField(default=False, verbose_name=_('مستقل'))  # اگر به هیچ کلینیکی وابسته نباشد
    is_available = models.BooleanField(default=True, verbose_name=_('در دسترس'))
    clinic = models.ForeignKey(Clinic, on_delete=models.SET_NULL, null=True, blank=True, related_name='doctors', verbose_name=_('کلینیک'))
    address = models.TextField(blank=True, null=True, verbose_name=_('آدرس'))
    phone = models.CharField(max_length=20, verbose_name=_('شماره تماس'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))

    class Meta:
        verbose_name = _('پزشک')
        verbose_name_plural = _('پزشکان')
        ordering = ['-created_at']

    def __str__(self):
        return f"دکتر {self.user.get_full_name()} - {self.specialization}"
    
    def get_available_slots(self, date):
        """محاسبه زمان‌های خالی برای یک تاریخ مشخص"""
        from reservations.models import Reservation, ReservationDay
        
        # دریافت روز هفته (0=شنبه، 6=جمعه)
        day_of_week = date.weekday()
        
        # دریافت تمام زمان‌بندی‌های این پزشک در این روز هفته
        day_availabilities = self.availabilities.filter(day_of_week=day_of_week)
        
        if not day_availabilities.exists():
            return []
        
        # بررسی اینکه آیا تاریخ منتشر شده است
        try:
            res_day = ReservationDay.objects.get(date=date)
            if not res_day.published:
                return []
        except ReservationDay.DoesNotExist:
            return []
        
        # دریافت تمام نوبت‌های این پزشک در این تاریخ
        reservations = Reservation.objects.filter(
            doctor=self,
            day__date=date,
            status__in=['pending', 'confirmed']
        )
        
        # دریافت زمان‌های رزرو شده
        reserved_times = [reservation.time for reservation in reservations]
        
        # تولید تمام زمان‌های ممکن (با فرض جلسات 30 دقیقه‌ای)
        slots = []
        
        for availability in day_availabilities:
            current_time = availability.start_time
            while current_time < availability.end_time:
                if current_time not in reserved_times:
                    slots.append(current_time)
                current_time = datetime.combine(datetime.today(), current_time) + timedelta(minutes=30)
                current_time = current_time.time()
        
        return sorted(slots)
    
    def calculate_earnings(self, start_date, end_date):
        """محاسبه درآمد پزشک در یک بازه زمانی"""
        from reservations.models import Reservation
        
        completed_reservations = Reservation.objects.filter(
            doctor=self,
            status='completed',
            payment_status='paid',
            day__date__gte=start_date,
            day__date__lte=end_date
        )
        
        return sum(res.amount for res in completed_reservations)

class DoctorAvailability(models.Model):
    DAYS_OF_WEEK = [
        (0, _('شنبه')),
        (1, _('یکشنبه')),
        (2, _('دوشنبه')),
        (3, _('سه‌شنبه')),
        (4, _('چهارشنبه')),
        (5, _('پنج‌شنبه')),
        (6, _('جمعه')),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='availabilities', verbose_name=_('پزشک'))
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, verbose_name=_('روز هفته'))
    start_time = models.TimeField(verbose_name=_('زمان شروع'))
    end_time = models.TimeField(verbose_name=_('زمان پایان'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))

    class Meta:
        verbose_name = _('زمان‌بندی پزشک')
        verbose_name_plural = _('زمان‌بندی‌های پزشکان')
        ordering = ['day_of_week', 'start_time']
        unique_together = ['doctor', 'day_of_week']

    def __str__(self):
        return f"{self.doctor} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
    
    def get_day_of_week_display(self):
        return dict(self.DAYS_OF_WEEK).get(self.day_of_week, '')
