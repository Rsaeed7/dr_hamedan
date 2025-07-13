import random
import uuid
from django.db.models import Avg, Count
from django_jalali.db import models as jmodels
from user.models import User
from clinics.models import Clinic
# from datetime import time, datetime, timedelta
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime, timedelta
import jdatetime
from khayyam import JalaliDate


class City(models.Model):
    name = models.CharField(max_length=50, verbose_name=_('نام شهر'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('شهر')
        verbose_name_plural = _('شهرها')


class Supplementary_insurance(models.Model):
    name = models.CharField(max_length=50, verbose_name=_('نام بیمه تکمیلی'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('بیمه تکمیلی')
        verbose_name_plural = _('بیمه های تکمیلی')


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
    GENDER_CHOICES = (('male', 'مرد'), ('female', 'زن'))
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_('کاربر'), related_name='doctor')
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True, verbose_name=_('تخصص'))
    license_number = models.CharField(max_length=50, unique=True, verbose_name=_('شماره پروانه'))
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, verbose_name=_('شهر محل خدمت'))
    bio = models.TextField(blank=True, verbose_name=_('بیوگرافی'))
    profile_image = models.ImageField(upload_to='doctor_profiles/', blank=True, null=True,
                                      verbose_name=_('تصویر پروفایل'))
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_('هزینه ویزیت'))
    consultation_duration = models.IntegerField(default=30, validators=[MinValueValidator(15), MaxValueValidator(120)],
                                                verbose_name=_('مدت زمان مشاوره (دقیقه)'))
    is_independent = models.BooleanField(default=False, verbose_name=_('مستقل'))  # اگر به هیچ کلینیکی وابسته نباشد
    is_available = models.BooleanField(default=True, verbose_name=_('در دسترس'))
    clinic = models.ForeignKey(Clinic, on_delete=models.SET_NULL, null=True, blank=True, related_name='doctors',
                               verbose_name=_('کلینیک'))
    address = models.TextField(blank=True, null=True, verbose_name=_('آدرس'))
    phone = models.CharField(max_length=20, verbose_name=_('شماره تماس'))
    Insurance = models.ManyToManyField(Supplementary_insurance, verbose_name=_('بیمه های تکمیلی طرف قرارداد'),
                                       blank=True, null=True)
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    gender = models.CharField(choices=GENDER_CHOICES, max_length=10, verbose_name=_('جنسیت'), null=True, blank=True)
    view_count = models.PositiveIntegerField(default=93, verbose_name='تعداد بازدید')
    online_visit = models.BooleanField(verbose_name='ویزیت آنلاین', default=True)
    online_visit_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                           verbose_name=_('هزینه ویزیت آنلاین'))
    # Geographic location fields
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True,
                                   verbose_name=_('عرض جغرافیایی'))
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True,
                                    verbose_name=_('طول جغرافیایی'))
    national_id = models.CharField(max_length=10, verbose_name=_('کد ملی'), blank=True, null=True)

    def get_first_available_day(self, max_days=30):
        """
        برگرداندن تاریخ شمسی اولین روزی که دکتر نوبت خالی دارد.
        :param max_days: بیشترین تعداد روزهایی که بررسی می‌شود.
        :return: jdatetime.date یا None اگر نوبت خالی پیدا نشد.
        """
        today = datetime.today().date()

        for i in range(max_days):
            date = today + timedelta(days=i)
            if self.get_available_slots(date):
                # تبدیل به تاریخ شمسی و برگشت
                return jdatetime.date.fromgregorian(date=date)

        return None

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
        """
        دریافت لیست زمان‌های آزاد برای یک تاریخ مشخص
        بر اساس نوبت‌های از پیش ایجاد شده
        """
        from reservations.models import ReservationDay, Reservation

        # تبدیل تاریخ جلالی به میلادی در صورت نیاز
        if hasattr(date, 'togregorian'):
            # اگر تاریخ جلالی است
            gregorian_date = date.togregorian()
        else:
            # اگر تاریخ میلادی است
            gregorian_date = date

        try:
            # پیدا کردن روز رزرو
            reservation_day = ReservationDay.objects.get(date=gregorian_date, published=True)
        except ReservationDay.DoesNotExist:
            return []

        # دریافت نوبت‌های آزاد برای این پزشک در این روز
        available_reservations = Reservation.objects.filter(
            day=reservation_day,
            doctor=self,
            status='available'
        ).order_by('time')

        # برگرداندن لیست زمان‌های آزاد
        return [reservation.time for reservation in available_reservations]

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

    def has_location(self):
        """Check if doctor has valid location coordinates"""
        return self.latitude is not None and self.longitude is not None

    def get_location_data(self):
        """Get location data for map display"""
        if self.has_location():
            return {
                'lat': float(self.latitude),
                'lng': float(self.longitude),
                'name': f"دکتر {self.user.get_full_name()}",
                'address': self.address or '',
                'specialization': self.specialization.name if self.specialization else '',
                'phone': self.phone or ''
            }
        return None


class DrServices(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='service', verbose_name='پزشک')
    service = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.service

    class Meta:
        verbose_name = 'خدمت'
        verbose_name_plural = 'خدمات'


class CommentTips(models.Model):
    tip = models.CharField(max_length=50, verbose_name='نکته')
    positive = models.BooleanField(default=True, verbose_name='نکته مثبت')

    def __str__(self):
        return self.tip

    class Meta:
        verbose_name = 'نکته'
        verbose_name_plural = 'نکات'


class DrComment(models.Model):
    STATUS_CHOICES = (('checking', 'در حال بررسی'), ('confirmed', 'تایید شده'))
    Recommendation_CHOICES = (('توصیه نمیکنم', 'توصیه نمیکنم'), ('توصیه میکنم', 'توصیه میکنم'))
    WAITING_CHOICES = (('کمتر از نیم ساعت', 'کمتر از نیم ساعت'), ('نیم تا یک ساعت', 'نیم تا یک ساعت'),
                       ('یک تا دو ساعت', 'یک تا دو ساعت'), ('بیش از دو ساعت', 'بیش از دو ساعت'))
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name='پزشک', related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر', related_name='doctor_comments',
                             null=True, blank=True)
    text = models.TextField(verbose_name='متن کامنت')
    recommendation = models.CharField(max_length=25, choices=Recommendation_CHOICES, verbose_name='توصیه',
                                      default=Recommendation_CHOICES[1], null=True, blank=True)
    rate = models.SmallIntegerField(verbose_name='امتیاز', blank=True, null=True,
                                    validators=[MinValueValidator(1), MaxValueValidator(5)])
    date = jmodels.jDateTimeField(verbose_name='تاریخ ثبت', auto_now_add=True)
    tips = models.ManyToManyField(CommentTips, related_name='comment_tips', verbose_name='نکات مثبت و منفی', blank=True,
                                  null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="checking", verbose_name="وضعیت")
    waiting_time = models.CharField(max_length=30, choices=WAITING_CHOICES, verbose_name="زمان انتظار",
                                    default=WAITING_CHOICES[1], blank=True, null=True)

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
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))

    class Meta:
        verbose_name = _('زمان‌بندی پزشک')
        verbose_name_plural = _('زمان‌بندی‌های پزشکان')
        ordering = ['day_of_week', 'start_time']
        unique_together = ['doctor', 'day_of_week']

    def __str__(self):
        return f"{self.doctor} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

    def get_day_of_week_display(self):
        return dict(self.DAYS_OF_WEEK).get(self.day_of_week, '')


class DoctorBlockedDay(models.Model):
    """
    روزهای مسدود شده توسط پزشک
    برای مسدود کردن تاریخ‌های خاص که در برنامه هفتگی پزشک موجود است
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='blocked_days', verbose_name=_('پزشک'))
    date = jmodels.jDateField(verbose_name=_('تاریخ مسدود شده'))
    reason = models.CharField(max_length=200, blank=True, verbose_name=_('دلیل'))
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))

    class Meta:
        verbose_name = _('روز مسدود شده')
        verbose_name_plural = _('روزهای مسدود شده')
        unique_together = ['doctor', 'date']
        ordering = ['-date']

    def __str__(self):
        reason_text = f" ({self.reason})" if self.reason else ""
        return f"{self.doctor.user.get_full_name()} - {self.date}{reason_text}"


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
    sent_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('زمان ارسال'))
    read_at = jmodels.jDateTimeField(null=True, blank=True, verbose_name=_('زمان خواندن'))
    is_read = models.BooleanField(default=False, verbose_name=_('خوانده شده'))
    is_important = models.BooleanField(default=False, verbose_name=_('مهم'))
    tracking_number = models.CharField(max_length=20, verbose_name=_('شماره رهگیری'), unique=True, blank=True,
                                       null=True)

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


class EmailTemplate(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='email_templates')
    title = models.CharField(max_length=200, verbose_name='عنوان قالب', blank=True, null=True)
    subject = models.CharField(max_length=200, verbose_name='موضوع', blank=True, null=True)
    body = models.TextField(verbose_name='متن نامه')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'قالب نامه'
        verbose_name_plural = 'قالب‌های نامه'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.subject} - {self.body:30}"


class DoctorRegistration(models.Model):
    """Model for doctor registration applications"""
    STATUS_CHOICES = (
        ('pending', 'در انتظار بررسی'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
    )

    # Personal Information
    first_name = models.CharField(max_length=50, verbose_name=_('نام'))
    last_name = models.CharField(max_length=50, verbose_name=_('نام خانوادگی'))
    email = models.EmailField(verbose_name=_('ایمیل'))
    phone = models.CharField(max_length=20, verbose_name=_('شماره تماس'))
    national_id = models.CharField(max_length=10, verbose_name=_('کد ملی'))
    gender = models.CharField(choices=Doctor.GENDER_CHOICES, max_length=10, verbose_name=_('جنسیت'))

    # Professional Information
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True, verbose_name=_('تخصص'))
    license_number = models.CharField(max_length=50, verbose_name=_('شماره پروانه'))
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, verbose_name=_('شهر محل خدمت'))
    bio = models.TextField(verbose_name=_('بیوگرافی'))
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('هزینه ویزیت'))
    consultation_duration = models.IntegerField(default=30, verbose_name=_('مدت زمان مشاوره (دقیقه)'))

    # Documents
    profile_image = models.ImageField(upload_to='doctor_registrations/profiles/', verbose_name=_('تصویر پروفایل'))
    license_image = models.ImageField(upload_to='doctor_registrations/licenses/', verbose_name=_('تصویر پروانه'))
    degree_image = models.ImageField(upload_to='doctor_registrations/degrees/', verbose_name=_('تصویر مدرک تحصیلی'))

    # Application Status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name=_('وضعیت'))
    admin_notes = models.TextField(blank=True, verbose_name=_('یادداشت‌های ادمین'))

    # Timestamps
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('تاریخ ثبت درخواست'))
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    reviewed_at = jmodels.jDateTimeField(null=True, blank=True, verbose_name=_('تاریخ بررسی'))
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reviewed_doctor_registrations', verbose_name=_('بررسی شده توسط'))

    class Meta:
        verbose_name = _('درخواست عضویت پزشک')
        verbose_name_plural = _('درخواست‌های عضویت پزشکان')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_status_display()}"

    def approve(self, admin_user):
        """Approve the doctor registration and create doctor profile"""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Create user account
        username = f"dr_{self.email.split('@')[0]}"
        password = User.objects.make_random_password()

        user = User.objects.create_user(
            username=username,
            email=self.email,
            first_name=self.first_name,
            last_name=self.last_name,
            phone=self.phone,
            user_type='doctor'
        )
        user.set_password(password)
        user.save()

        # Create doctor profile
        doctor = Doctor.objects.create(
            user=user,
            specialization=self.specialization,
            license_number=self.license_number,
            national_id=self.national_id,
            city=self.city,
            bio=self.bio,
            profile_image=self.profile_image,
            consultation_fee=self.consultation_fee,
            consultation_duration=self.consultation_duration,
            phone=self.phone,
            gender=self.gender,
            is_available=True
        )

        # Update registration status
        self.status = 'approved'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()
        
        # Send approval SMS with credentials using centralized SMS service
        from utils.sms_service import sms_service
        sms_service.send_doctor_approval(user, username, password)
        
        return doctor

    def reject(self, admin_user, reason=""):
        """Reject the doctor registration"""
        self.status = 'rejected'
        self.admin_notes = reason
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()


class Notification(models.Model):
    """
    مدل اعلان‌ها برای پزشکان
    """
    NOTIFICATION_TYPES = (
        ('info', 'اطلاعات'),
        ('success', 'موفقیت'),
        ('warning', 'هشدار'),
        ('error', 'خطا'),
        ('appointment', 'نوبت'),
        ('message', 'پیام'),
        ('system', 'سیستم'),
    )

    PRIORITY_CHOICES = (
        ('low', 'کم'),
        ('medium', 'متوسط'),
        ('high', 'زیاد'),
        ('urgent', 'فوری'),
    )

    # اطلاعات اصلی
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('کاربر')
    )
    title = models.CharField(max_length=200, verbose_name=_('عنوان'))
    message = models.TextField(verbose_name=_('متن پیام'))
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='info',
        verbose_name=_('نوع اعلان')
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=_('اولویت')
    )

    # وضعیت خواندن
    is_read = models.BooleanField(default=False, verbose_name=_('خوانده شده'))
    read_at = jmodels.jDateTimeField(null=True, blank=True, verbose_name=_('زمان خواندن'))

    # لینک اختیاری
    link = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_('لینک مرتبط')
    )

    # اطلاعات اضافی
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('داده‌های اضافی')
    )

    # تاریخ‌ها
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    expires_at = jmodels.jDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('تاریخ انقضا')
    )

    # نمایش
    is_visible = models.BooleanField(default=True, verbose_name=_('قابل نمایش'))

    class Meta:
        verbose_name = _('اعلان')
        verbose_name_plural = _('اعلان‌ها')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['priority', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"

    def mark_as_read(self):
        """علامت‌گذاری به عنوان خوانده شده"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def mark_as_unread(self):
        """علامت‌گذاری به عنوان خوانده نشده"""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at'])

    def is_expired(self):
        """بررسی انقضای اعلان"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def get_priority_class(self):
        """کلاس CSS برای اولویت"""
        priority_classes = {
            'low': 'text-secondary',
            'medium': 'text-primary',
            'high': 'text-warning',
            'urgent': 'text-danger'
        }
        return priority_classes.get(self.priority, 'text-primary')

    def get_type_icon(self):
        """آیکون بر اساس نوع اعلان"""
        icons = {
            'info': 'fa-info-circle',
            'success': 'fa-check-circle',
            'warning': 'fa-exclamation-triangle',
            'error': 'fa-times-circle',
            'appointment': 'fa-calendar-check',
            'message': 'fa-envelope',
            'system': 'fa-cog'
        }
        return icons.get(self.notification_type, 'fa-bell')

    def get_type_color(self):
        """رنگ بر اساس نوع اعلان"""
        colors = {
            'info': 'info',
            'success': 'success',
            'warning': 'warning',
            'error': 'danger',
            'appointment': 'primary',
            'message': 'secondary',
            'system': 'dark'
        }
        return colors.get(self.notification_type, 'info')

    @classmethod
    def create_notification(cls, user, title, message, notification_type='info', priority='medium', link=None,
                            metadata=None, expires_at=None):
        """
        ایجاد اعلان جدید
        """
        return cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            link=link,
            metadata=metadata or {},
            expires_at=expires_at
        )

    @classmethod
    def get_user_notifications(cls, user, unread_only=False, limit=None):
        """
        دریافت اعلان‌های کاربر
        """
        notifications = cls.objects.filter(
            user=user,
            is_visible=True
        )

        if unread_only:
            notifications = notifications.filter(is_read=False)

        # حذف اعلان‌های منقضی شده
        notifications = notifications.filter(
            models.Q(expires_at__isnull=True) |
            models.Q(expires_at__gt=timezone.now())
        )

        notifications = notifications.order_by('-created_at')

        if limit:
            notifications = notifications[:limit]

        return notifications

    @classmethod
    def get_unread_count(cls, user):
        """
        تعداد اعلان‌های خوانده نشده
        """
        return cls.objects.filter(
            user=user,
            is_read=False,
            is_visible=True
        ).filter(
            models.Q(expires_at__isnull=True) |
            models.Q(expires_at__gt=timezone.now())
        ).count()

    @classmethod
    def mark_all_as_read(cls, user):
        """
        علامت‌گذاری همه اعلان‌ها به عنوان خوانده شده
        """
        cls.objects.filter(
            user=user,
            is_read=False,
            is_visible=True
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

    @classmethod
    def cleanup_expired(cls):
        """
        پاک کردن اعلان‌های منقضی شده
        """
        expired_notifications = cls.objects.filter(
            expires_at__lt=timezone.now()
        )
        count = expired_notifications.count()
        expired_notifications.delete()
        return count

