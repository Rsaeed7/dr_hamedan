import random
import uuid

from django.db import models
# from django.contrib.auth.models import User
from django.db.models import Avg, Count
from user.models import User
from clinics.models import Clinic
from datetime import time, datetime, timedelta
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class City(models.Model):
    name = models.CharField(max_length=50, verbose_name=_('نام شهر'))
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('شهر')
        verbose_name_plural = _('شهرها')

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
    GENDER_CHOICES = (('male','مرد'),('female','زن'))
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_('کاربر'), related_name='doctor')
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True, verbose_name=_('تخصص'))
    license_number = models.CharField(max_length=50, unique=True, verbose_name=_('شماره پروانه'))
    city = models.ForeignKey(City,on_delete=models.SET_NULL, null=True, verbose_name=_('شهر محل خدمت'))
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
    gender = models.CharField(choices=GENDER_CHOICES, max_length=10, verbose_name=_('جنسیت'), null=True, blank=True)
    view_count = models.PositiveIntegerField(default=93, verbose_name='تعداد بازدید')

    def increment_view_count(self):
        """افزایش تعداد بازدیدها"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def comment_rate(self, decimal_places=1, default=None):
        """محاسبه امتیاز پزشک بر اساس کامنت‌های تایید شده"""
        result = DrComment.objects.filter(
            doctor=self,
            status='confirmed'
        ).aggregate(
            avg_rate=Avg('rate'),
            count=Count('id')
        )

        if result['avg_rate'] is None:
            return 4.0

        return round(result['avg_rate'], decimal_places)

    @property
    def comment_stats(self):
        """آمار کامل نظرات برای استفاده در ویوها"""
        stats = DrComment.objects.filter(
            doctor=self,
            status='confirmed'
        ).aggregate(
            avg_rate=Avg('rate'),
            count=Count('id')
        )

        return {
            'average': stats['avg_rate'],
            'count': stats['count'],
            'has_rating': stats['count'] > 0
        }

    def recommendation_percentage(self):
        """محاسبه درصد توصیه شده بر اساس کامنت ها"""
        confirmed_comments = self.comments.filter(status='confirmed')
        total = confirmed_comments.count()
        positive = confirmed_comments.filter(recommendation='توصیه میکنم').count()

        if total == 0:
            return 90

        percentage = (positive / total) * 100

        # اگر عدد صحیح است، بدون اعشار برگردان
        if percentage.is_integer():
            return int(percentage)
        return round(percentage, 1)

    def get_most_common_waiting_time(self):
        """محاسبه زمان‌ انتظار در مطب بر اساس کامنت ها"""
        from collections import Counter
        waiting_times = self.comments.filter(status='confirmed').values_list('waiting_time', flat=True)

        if not waiting_times:
            return "نیم تا یک ساعت"

        # یافتن پرتکرارترین مقدار
        counter = Counter(waiting_times)
        most_common = counter.most_common(1)[0][0]

        return most_common

    class Meta:
        verbose_name = _('پزشک')
        verbose_name_plural = _('پزشکان')
        ordering = ['-created_at']

    def __str__(self):
        return f"دکتر {self.user.name} - {self.specialization}"
    
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

class DrServices(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='service', verbose_name='پزشک')
    service = models.CharField(max_length=50,null=True,blank=True)

    def __str__(self):
        return self.service

    class Meta:
        verbose_name = 'خدمت'
        verbose_name_plural = 'خدمات'

class CommentTips(models.Model):
    tip = models.CharField(max_length=50 , verbose_name='نکته')
    positive = models.BooleanField(default=True , verbose_name='نکته مثبت')

    def __str__(self):
        return self.tip

    class Meta:
        verbose_name = 'نکته'
        verbose_name_plural = 'نکات'

class DrComment(models.Model):
    STATUS_CHOICES = (('checking','در حال بررسی'),('confirmed','تایید شده'))
    Recommendation_CHOICES = (('توصیه نمیکنم','توصیه نمیکنم'),('توصیه میکنم','توصیه میکنم'))
    WAITING_CHOICES = (('کمتر از نیم ساعت','کمتر از نیم ساعت'),('نیم تا یک ساعت','نیم تا یک ساعت'),('یک تا دو ساعت','یک تا دو ساعت'),('بیش از دو ساعت','بیش از دو ساعت'))
    doctor = models.ForeignKey(Doctor , on_delete=models.CASCADE , verbose_name='پزشک', related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر', related_name='doctor_comments', null=True, blank=True)
    text = models.TextField(verbose_name='متن کامنت')
    recommendation = models.CharField(max_length=25, choices=Recommendation_CHOICES, verbose_name='توصیه',default=Recommendation_CHOICES[1], null=True, blank=True)
    rate = models.SmallIntegerField(verbose_name='امتیاز', blank=True, null=True,validators=[MinValueValidator(1), MaxValueValidator(5)])
    date = models.DateTimeField(verbose_name='تاریخ ثبت', auto_now_add=True)
    tips = models.ManyToManyField(CommentTips, related_name='comment_tips' , verbose_name='نکات مثبت و منفی', blank=True,null=True)
    status = models.CharField( max_length=10, choices=STATUS_CHOICES, default="checking", verbose_name="وضعیت")
    waiting_time = models.CharField(max_length=30,choices=WAITING_CHOICES, verbose_name="زمان انتظار",default=WAITING_CHOICES[1])

    class Meta:
        ordering = ("date",)
        verbose_name = "کامنت"
        verbose_name_plural = "کامنت ها"


    def __str__(self):
        return f'from "{self.user}" to "{self.doctor}"'

    def status_display(self):
        if self.status == 'checking':
            return 'در حال بررسی'
        else:
            return 'تایید شده'

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

class Email(models.Model):
    sender = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name=_('فرستنده')
    )
    recipient = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name=_('گیرنده')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.CharField(max_length=200, verbose_name=_('موضوع'))
    body = models.TextField(verbose_name=_('متن نامه'))
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name=_('زمان ارسال'))
    read_at = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان خواندن'))
    is_read = models.BooleanField(default=False, verbose_name=_('خوانده شده'))
    is_important = models.BooleanField(default=False, verbose_name=_('مهم'))
    tracking_number = models.CharField(
        max_length=5,
        unique=True,
        editable=False,
        verbose_name=_('شماره رهگیری')
    )



    class Meta:
        verbose_name = _('نامه')
        verbose_name_plural = _('نامه‌ها')
        ordering = ['-sent_at']
        constraints = [
            models.CheckConstraint(
                check=~models.Q(sender=models.F('recipient')),
                name='prevent_self_message'
            )
        ]

    def __str__(self):
        return f"{self.subject} - {self.sender.user.get_full_name()} به {self.recipient.user.get_full_name()}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def mark_as_unread(self):
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save()

    def toggle_importance(self):
        self.is_important = not self.is_important
        self.save()

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            while True:
                code = str(random.randint(10000, 99999))  # عدد ۵ رقمی
                if not Email.objects.filter(tracking_number=code).exists():
                    self.tracking_number = code
                    break

        super().save(*args, **kwargs)


