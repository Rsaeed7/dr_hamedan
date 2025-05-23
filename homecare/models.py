from django.db import models
from django_jalali.db import models as jmodels
from doctors.models import City
from patients.models import PatientsFile

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="عنوان دسته")
    icon = models.ImageField(verbose_name="آیکن", upload_to="services", null=True, blank=True)
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "دسته خدمات"
        verbose_name_plural = "دسته‌های خدمات"

class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=100, verbose_name="نام خدمت")
    icon = models.ImageField(verbose_name="آیکن", upload_to="services", null=True, blank=True)
    description = models.TextField(blank=True, verbose_name="توضیحات")
    estimated_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="هزینه حدودی (تومان)")
    requires_prescription = models.BooleanField(default=False, verbose_name="نیاز به نسخه دارد؟")
    available_in_cities = models.ManyToManyField(City, related_name="homecare_services")

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    class Meta:
        verbose_name = "خدمت"
        verbose_name_plural = "خدمات"

class HomeCareRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار بررسی'),
        ('contacted', 'تماس گرفته شده'),
        ('confirmed', 'تایید شده'),
        ('rejected', 'رد شده'),
        ('cancelled_by_patient', 'لغو توسط بیمار'),
    ]

    patient = models.ForeignKey(PatientsFile, on_delete=models.CASCADE, verbose_name="بیمار")
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, verbose_name="خدمت درخواستی")
    requested_date = jmodels.jDateField(verbose_name="تاریخ مورد نظر")
    requested_time = models.TimeField(verbose_name="ساعت مورد نظر")
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    address = models.TextField(verbose_name="آدرس دقیق بیمار")
    extra_notes = models.TextField(blank=True, verbose_name="توضیحات اضافی")
    prescription_file = models.FileField(upload_to='prescriptions/', blank=True, null=True, verbose_name="فایل نسخه")
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="وضعیت درخواست")

    def __str__(self):
        return f"{self.patient.user.name} - {self.service} - {self.requested_date}"

    class Meta:
        verbose_name = "درخواست خدمات در محل"
        verbose_name_plural = "درخواست‌های خدمات در محل"
