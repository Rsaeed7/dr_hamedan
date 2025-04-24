from django.db import models
from django.contrib.auth.models import User

class Clinic(models.Model):
    name = models.CharField(max_length=255, verbose_name='نام')
    address = models.TextField(verbose_name='آدرس')
    phone = models.CharField(max_length=20, verbose_name='شماره تماس')
    email = models.EmailField(verbose_name='ایمیل')
    logo = models.ImageField(upload_to='clinic_logos/', blank=True, null=True, verbose_name='لوگو')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='administered_clinics', verbose_name='مدیر')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    def __str__(self):
        return self.name
    
    def get_doctors(self):
        return self.doctors.all()
    
    def get_all_appointments(self):
        from reservations.models import Reservation
        doctors = self.get_doctors()
        return Reservation.objects.filter(doctor__in=doctors)

    class Meta:
        verbose_name = 'کلینیک'
        verbose_name_plural = 'کلینیک‌ها'

class ClinicSpecialty(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='specialties', verbose_name='کلینیک')
    name = models.CharField(max_length=255, verbose_name='نام')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')

    def __str__(self):
        return f"{self.clinic.name} - {self.name}"
    
    class Meta:
        verbose_name = 'تخصص کلینیک'
        verbose_name_plural = 'تخصص‌های کلینیک'

class ClinicGallery(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='gallery', verbose_name='کلینیک')
    image = models.ImageField(upload_to='clinic_gallery/', verbose_name='تصویر')
    title = models.CharField(max_length=255, blank=True, null=True, verbose_name='عنوان')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    def __str__(self):
        return f"{self.clinic.name} Gallery Image - {self.id}"
    
    class Meta:
        verbose_name = 'گالری کلینیک'
        verbose_name_plural = 'گالری‌های کلینیک'
