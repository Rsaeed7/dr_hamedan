from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(_('تخصص'), max_length=100)
    bio = models.TextField(_('بیوگرافی'), blank=True, null=True)
    profile_image = models.ImageField(_('تصویر پروفایل'), upload_to='doctors/', blank=True, null=True)
    consultation_fee = models.DecimalField(_('هزینه ویزیت'), max_digits=10, decimal_places=2)
    is_independent = models.BooleanField(_('مستقل'), default=True)
    is_available = models.BooleanField(_('فعال'), default=True)
    clinic = models.ForeignKey('clinics.Clinic', on_delete=models.SET_NULL, related_name='doctors', null=True, blank=True, verbose_name=_('کلینیک'))
    
    # Office/clinic contact info
    address = models.TextField(_('آدرس مطب'), blank=True, null=True)
    phone = models.CharField(_('تلفن مطب'), max_length=15, blank=True, null=True)
    
    class Meta:
        verbose_name = _('پزشک')
        verbose_name_plural = _('پزشکان')
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username}"
    
    def get_available_slots(self, date):
        """Returns available time slots for a specific date"""
        # Implementation to be added
        pass
    
    def get_earnings(self, period=None):
        """Calculate doctor's earnings for a given period"""
        # Implementation to be added
        pass


class DoctorAvailability(models.Model):
    """Model to track when a doctor is available for appointments"""
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(_('روز هفته'), choices=[
        (0, _('دوشنبه')),
        (1, _('سه شنبه')),
        (2, _('چهارشنبه')),
        (3, _('پنجشنبه')),
        (4, _('جمعه')),
        (5, _('شنبه')),
        (6, _('یکشنبه')),
    ])
    start_time = models.TimeField(_('زمان شروع'))
    end_time = models.TimeField(_('زمان پایان'))
    
    class Meta:
        verbose_name = _('زمان حضور پزشک')
        verbose_name_plural = _('زمان های حضور پزشک')
        
    def __str__(self):
        day_names = ['دوشنبه', 'سه شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه', 'شنبه', 'یکشنبه']
        return f"{self.doctor} - {day_names[self.day_of_week]} {self.start_time} تا {self.end_time}"
