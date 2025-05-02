from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, EmailValidator




class Clinic(models.Model):
    name = models.CharField(max_length=255, verbose_name='نام')
    address = models.TextField(verbose_name='آدرس')
    phone = models.CharField(max_length=20, verbose_name='شماره تماس')
    email = models.EmailField(verbose_name='ایمیل',validators=[EmailValidator()])
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

    def recommendation_percentage(self):

        confirmed_comments = self.comments.filter(status='confirmed')
        total = confirmed_comments.count()
        positive = confirmed_comments.filter(recommendation=' توصیه میکنم').count()

        if total == 0:
            return 90

        percentage = (positive / total) * 100

        # اگر عدد صحیح است، بدون اعشار برگردان
        if percentage.is_integer():
            return int(percentage)
        return round(percentage, 1)
    def comment_rate(self, decimal_places=2):
        from django.db.models import Avg

        result = ClinicComment.objects.filter(
            clinic=self ,status='confirmed'
        ).aggregate(
            avg_rate=Avg('rate')
        )

        avg_rate = result['avg_rate'] if result['avg_rate'] is not None else 4.0
        return round(avg_rate, decimal_places)


    class Meta:
        verbose_name = 'کلینیک'
        verbose_name_plural = 'کلینیک‌ها'



class ClinicSpecialty(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='specialties', verbose_name='کلینیک')
    name = models.CharField(max_length=255, verbose_name='نام تخصص')
    Doctor = models.ManyToManyField('doctors.Doctor', related_name='special_doctors', verbose_name= 'پزشکان', blank=True,null=True)
    # Doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE)

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






class ClinicComment(models.Model):
    STATUS_CHOICES = (('checking','در حال بررسی'),('confirmed','تایید شده'))
    Recommendation_CHOICES = (('توصیه نمیکنم','توصیه نمیکنم'),('توصیه میکنم','توصیه میکنم'))
    clinic = models.ForeignKey(Clinic , on_delete=models.CASCADE , verbose_name='کلینیک', related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر', related_name='product_comments', null=True, blank=True)
    text = models.TextField(verbose_name='متن کامنت')
    recommendation = models.CharField(max_length=25, choices=Recommendation_CHOICES, verbose_name='توصیه',default=Recommendation_CHOICES[1], null=True, blank=True)
    rate = models.SmallIntegerField(verbose_name='امتیاز', blank=True, null=True,validators=[MinValueValidator(1), MaxValueValidator(5)])
    date = models.DateTimeField(verbose_name='تاریخ ثبت', auto_now_add=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="checking", verbose_name="وضعیت"
    )

    class Meta:
        ordering = ("date",)
        verbose_name = "کامنت"
        verbose_name_plural = "کامنت ها"


    def __str__(self):
        return f'from "{self.user}" to "{self.clinic}"'

    def status_display(self):
        if self.status == 'checking':
            return 'در حال بررسی'
        else:
            return 'تایید شده'


