from django.db import models
from django.contrib.auth.models import User

class PatientsFile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='کاربر')
    name = models.CharField(max_length=255, verbose_name='نام')
    phone = models.CharField(max_length=20, verbose_name='شماره تلفن')
    national_id = models.CharField(max_length=20, blank=True, null=True, verbose_name='کد ملی')
    medical_history = models.TextField(blank=True, null=True, verbose_name='سابقه پزشکی')
    notes = models.TextField(blank=True, null=True, verbose_name='یادداشت‌ها')
    birthdate = models.DateField(blank=True, null=True, verbose_name='تاریخ تولد')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    
    class Meta:
        verbose_name = 'پرونده بیمار'
        verbose_name_plural = 'پرونده‌های بیماران'
    
    def __str__(self):
        return self.name
    
    def get_reservations(self):
        """Get all reservations for this patient"""
        from reservations.models import Reservation
        return Reservation.objects.filter(patient=self)
    
    def get_upcoming_appointments(self):
        """Get upcoming appointments for this patient"""
        from reservations.models import Reservation
        from django.utils import timezone
        
        return Reservation.objects.filter(
            patient=self,
            status__in=['pending', 'confirmed'],
            day__date__gte=timezone.now().date()
        ).order_by('day__date', 'time')
    
    def get_past_appointments(self):
        """Get past appointments for this patient"""
        from reservations.models import Reservation
        from django.utils import timezone
        
        return Reservation.objects.filter(
            patient=self,
            day__date__lt=timezone.now().date()
        ).order_by('-day__date', '-time')
