import base64
import uuid
from datetime import date

from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from django_jalali.db import models as jmodels
from doctors.models import Doctor
from doctors.models import City
from user.models import User
import jdatetime

class PatientsFile(models.Model):
    GENDER_CHOICES = (('male', 'مرد'), ('female', 'زن'))
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='کاربر', related_name='patient')
    phone = models.CharField(max_length=20, verbose_name='شماره تلفن')
    national_id = models.CharField(max_length=20, blank=True, null=True, verbose_name='کد ملی')
    medical_history = models.TextField(blank=True, null=True, verbose_name='سابقه پزشکی')
    birthdate = jmodels.jDateField(blank=True, null=True, verbose_name='تاریخ تولد')
    gender = models.CharField(choices=GENDER_CHOICES,max_length=10, blank=True, null=True , verbose_name='جنسیت')
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    city = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True, verbose_name='شهر')
    email = models.EmailField(verbose_name='ایمیل', blank=True, null=True)
    
    class Meta:
        verbose_name = 'پرونده بیمار'
        verbose_name_plural = 'پرونده‌های بیماران'
    

    
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

    @property
    def age(self):
        """ محاسبه سن بیمار بر اساس تاریخ تولد """
        if not self.birthdate:
            return '-'
        today = jdatetime.date.today()
        age = today.year - self.birthdate.year - (
                (today.month, today.day) < (self.birthdate.month, self.birthdate.day)
        )
        return age  # مقدار نهایی سن بیمار

    @property
    def name(self):
        return self.user.first_name + ' ' + self.user.last_name


    def __str__(self):
        return f"{self.user}"



class MedicalRecord(models.Model):
    patient = models.ForeignKey(PatientsFile, on_delete=models.CASCADE, related_name='records', verbose_name='بیمار')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='records', verbose_name='پزشک')
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد پرونده')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'پرونده پزشکی'
        verbose_name_plural = 'پرونده‌های پزشکی'
        unique_together = ('patient', 'doctor')

    def __str__(self):
        return f"پرونده {self.patient.name} - دکتر {self.doctor}"


class VisitEntry(models.Model):
    record = models.ForeignKey('MedicalRecord', on_delete=models.CASCADE, related_name='visits', verbose_name='پرونده')
    visit_date = jmodels.jDateTimeField(default=timezone.now, verbose_name='تاریخ ویزیت')
    chief_complaint = models.TextField(verbose_name='شرح مشکل')
    diagnosis = models.TextField(blank=True, null=True, verbose_name='تشخیص')
    physical_exam = models.TextField(blank=True, null=True, verbose_name='معاینه بالینی')
    treatment_plan = models.TextField(blank=True, null=True, verbose_name='طرح درمان')
    prescribed_medications = models.TextField(blank=True, null=True, verbose_name='داروهای تجویزی')
    notes = models.TextField(blank=True, null=True, verbose_name='یادداشت تکمیلی')
    attachment = models.FileField(upload_to='visit_attachments/', null=True, blank=True, verbose_name='فایل پیوست')
    handwritten_image = models.ImageField(
        upload_to='handwritten_notes/%Y/%m/%d/',  # سازماندهی فایل‌ها بر اساس تاریخ
        null=True,
        blank=True,
        verbose_name='یادداشت دستی'
    )

    def save_sketch(self, data_url):
        """تبدیل داده Base64 به فایل تصویری"""
        if data_url:
            # جدا کردن هدر و داده اصلی
            format, imgstr = data_url.split(';base64,')
            ext = format.split('/')[-1]  # استخراج پسوند (png/jpeg)

            # ایجاد نام منحصر به فرد
            filename = f"sketch_{uuid.uuid4().hex[:8]}.{ext}"

            # ذخیره فایل
            self.handwritten_image.save(
                filename,
                ContentFile(base64.b64decode(imgstr)),
                save=False
            )

    class Meta:
        verbose_name = 'ویزیت'
        verbose_name_plural = 'ویزیت‌ها'
        ordering = ['-visit_date']

    def __str__(self):
        return f"{self.record.patient.name} - {self.visit_date.date()}"



class MedicalReport(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='reports')
    patient = models.ForeignKey(PatientsFile, on_delete=models.CASCADE, related_name='reports',blank=True, null=True)
    name = models.CharField(max_length=50, verbose_name='نام بیمار')
    title = models.CharField(max_length=200,blank=True,null=True,verbose_name="عنوان")
    dr_requesting = models.CharField(max_length=50,blank=True,null=True,verbose_name='پزشک درخواست کننده')
    content = models.TextField(verbose_name='شرح')  # متن گزارش
    age = models.IntegerField(blank=True,null=True,verbose_name='سن بیمار')
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    updated_at = jmodels.jDateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.patient}"

class ReportImage(models.Model):
    report = models.ForeignKey(MedicalReport, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='report_images/')
    caption = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Image for {self.report.title}"



class DrReportSettings(models.Model):
    doctor = models.OneToOneField(Doctor, on_delete=models.CASCADE, related_name='template_settings')
    background_image = models.ImageField(upload_to='doctor_templates/', blank=True, null=True, verbose_name="تصویر پس‌زمینه")
    custom_css = models.TextField(blank=True, null=True, verbose_name="استایل سفارشی")

    def __str__(self):
        return f"تنظیمات قالب ریپورت{self.doctor}"


class ReportTemplate(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='report_templates')
    title = models.CharField(max_length=100, verbose_name="عنوان قالب",blank=True,null=True,default='قالب آماده')
    dr_requesting = models.CharField(max_length=50, blank=True, null=True, verbose_name='پزشک درخواست کننده',default=' ')
    content = models.TextField(verbose_name="متن گزارش")

    def __str__(self):
        return f"{self.title} - {self.content:30}"
