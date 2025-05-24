from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django_jalali.db import models as jmodels
from decimal import Decimal
from django.utils import timezone
from user.models import User
from doctors.models import Doctor, Specialization
from clinics.models import Clinic


class DiscountType(models.Model):
    """نوع تخفیف"""
    DISCOUNT_TYPES = (
        ('percentage', 'درصدی'),
        ('fixed_amount', 'مبلغ ثابت'),
        ('buy_one_get_one', 'یکی بخر یکی بگیر'),
    )
    
    name = models.CharField(max_length=100, verbose_name=_('نام نوع تخفیف'))
    type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, verbose_name=_('نوع'))
    description = models.TextField(blank=True, verbose_name=_('توضیحات'))
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    
    class Meta:
        verbose_name = _('نوع تخفیف')
        verbose_name_plural = _('انواع تخفیف')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Discount(models.Model):
    """تخفیف"""
    APPLICABLE_TO_CHOICES = (
        ('all', 'همه خدمات'),
        ('doctor', 'پزشک خاص'),
        ('specialization', 'تخصص خاص'),
        ('clinic', 'کلینیک خاص'),
        ('first_time', 'بیماران جدید'),
        ('returning', 'بیماران قدیمی'),
    )
    
    STATUS_CHOICES = (
        ('active', 'فعال'),
        ('inactive', 'غیرفعال'),
        ('expired', 'منقضی شده'),
        ('used_up', 'استفاده شده'),
    )
    
    title = models.CharField(max_length=200, verbose_name=_('عنوان تخفیف'))
    description = models.TextField(verbose_name=_('توضیحات'))
    discount_type = models.ForeignKey(DiscountType, on_delete=models.CASCADE, verbose_name=_('نوع تخفیف'))
    
    # تخفیف درصدی یا مبلغ ثابت
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('درصد تخفیف')
    )
    fixed_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_('مبلغ ثابت تخفیف')
    )
    
    # شرایط اعمال تخفیف
    applicable_to = models.CharField(max_length=20, choices=APPLICABLE_TO_CHOICES, verbose_name=_('قابل اعمال برای'))
    doctors = models.ManyToManyField(Doctor, blank=True, verbose_name=_('پزشکان'))
    specializations = models.ManyToManyField(Specialization, blank=True, verbose_name=_('تخصص‌ها'))
    clinics = models.ManyToManyField(Clinic, blank=True, verbose_name=_('کلینیک‌ها'))
    
    # محدودیت‌های تخفیف
    min_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_('حداقل مبلغ سفارش')
    )
    max_discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_('حداکثر مبلغ تخفیف')
    )
    
    # تاریخ‌های اعتبار
    start_date = jmodels.jDateTimeField(verbose_name=_('تاریخ شروع'))
    end_date = jmodels.jDateTimeField(verbose_name=_('تاریخ پایان'))
    
    # محدودیت استفاده
    usage_limit = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('محدودیت استفاده کل'))
    usage_limit_per_user = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('محدودیت استفاده هر کاربر'))
    used_count = models.PositiveIntegerField(default=0, verbose_name=_('تعداد استفاده'))
    
    # وضعیت
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name=_('وضعیت'))
    is_public = models.BooleanField(default=True, verbose_name=_('عمومی'))
    
    # اطلاعات اضافی
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_('ایجاد شده توسط'))
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    
    class Meta:
        verbose_name = _('تخفیف')
        verbose_name_plural = _('تخفیفات')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def is_valid(self):
        """بررسی معتبر بودن تخفیف"""
        now = timezone.now()
        return (
            self.status == 'active' and
            self.start_date <= now <= self.end_date and
            (self.usage_limit is None or self.used_count < self.usage_limit)
        )
    
    def can_be_used_by_user(self, user):
        """بررسی امکان استفاده توسط کاربر"""
        if not self.is_valid():
            return False
        
        if self.usage_limit_per_user is None:
            return True
        
        user_usage_count = DiscountUsage.objects.filter(
            discount=self, user=user
        ).count()
        
        return user_usage_count < self.usage_limit_per_user
    
    def calculate_discount(self, amount):
        """محاسبه مبلغ تخفیف"""
        if not self.is_valid():
            return Decimal('0')
        
        if self.min_amount and amount < self.min_amount:
            return Decimal('0')
        
        if self.discount_type.type == 'percentage':
            discount_amount = amount * (Decimal(str(self.percentage)) / Decimal('100'))
        elif self.discount_type.type == 'fixed_amount':
            discount_amount = self.fixed_amount
        else:
            return Decimal('0')
        
        # اعمال حداکثر مبلغ تخفیف
        if self.max_discount_amount and discount_amount > self.max_discount_amount:
            discount_amount = self.max_discount_amount
        
        return min(discount_amount, amount)
    
    def apply_to_reservation(self, reservation, user):
        """اعمال تخفیف به رزرو"""
        if not self.can_be_used_by_user(user):
            return False, "امکان استفاده از این تخفیف وجود ندارد"
        
        # بررسی قابلیت اعمال تخفیف
        if not self._is_applicable_to_reservation(reservation):
            return False, "این تخفیف برای این نوبت قابل اعمال نیست"
        
        discount_amount = self.calculate_discount(reservation.amount)
        if discount_amount == 0:
            return False, "مبلغ تخفیف صفر است"
        
        # ایجاد رکورد استفاده از تخفیف
        DiscountUsage.objects.create(
            discount=self,
            user=user,
            reservation=reservation,
            discount_amount=discount_amount,
            original_amount=reservation.amount
        )
        
        # بروزرسانی تعداد استفاده
        self.used_count += 1
        self.save()
        
        return True, f"تخفیف {discount_amount} تومان اعمال شد"
    
    def _is_applicable_to_reservation(self, reservation):
        """بررسی قابلیت اعمال تخفیف به رزرو"""
        if self.applicable_to == 'all':
            return True
        elif self.applicable_to == 'doctor':
            return reservation.doctor in self.doctors.all()
        elif self.applicable_to == 'specialization':
            return reservation.doctor.specialization in self.specializations.all()
        elif self.applicable_to == 'clinic':
            return reservation.doctor.clinic in self.clinics.all()
        elif self.applicable_to == 'first_time':
            # بیمار جدید
            previous_reservations = reservation.patient.reservations.exclude(id=reservation.id)
            return not previous_reservations.exists()
        elif self.applicable_to == 'returning':
            # بیمار قدیمی
            previous_reservations = reservation.patient.reservations.exclude(id=reservation.id)
            return previous_reservations.exists()
        
        return False


class CouponCode(models.Model):
    """کد تخفیف"""
    code = models.CharField(max_length=50, unique=True, verbose_name=_('کد تخفیف'))
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE, related_name='coupon_codes', verbose_name=_('تخفیف'))
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    
    class Meta:
        verbose_name = _('کد تخفیف')
        verbose_name_plural = _('کدهای تخفیف')
        ordering = ['code']
    
    def __str__(self):
        return self.code
    
    def is_valid(self):
        """بررسی معتبر بودن کد تخفیف"""
        return self.is_active and self.discount.is_valid()


class DiscountUsage(models.Model):
    """استفاده از تخفیف"""
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE, related_name='usages', verbose_name=_('تخفیف'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discount_usages', verbose_name=_('کاربر'))
    reservation = models.OneToOneField('reservations.Reservation', on_delete=models.CASCADE, related_name='discount_usage', verbose_name=_('رزرو'))
    coupon_code = models.ForeignKey(CouponCode, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('کد تخفیف'))
    
    original_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('مبلغ اصلی'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('مبلغ تخفیف'))
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('مبلغ نهایی'))
    
    used_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('تاریخ استفاده'))
    
    class Meta:
        verbose_name = _('استفاده از تخفیف')
        verbose_name_plural = _('استفاده‌های تخفیف')
        ordering = ['-used_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.discount.title} - {self.discount_amount} تومان"
    
    def save(self, *args, **kwargs):
        if not self.final_amount:
            self.final_amount = self.original_amount - self.discount_amount
        super().save(*args, **kwargs)


class AutomaticDiscount(models.Model):
    """تخفیف خودکار"""
    name = models.CharField(max_length=100, verbose_name=_('نام'))
    discount = models.OneToOneField(Discount, on_delete=models.CASCADE, verbose_name=_('تخفیف'))
    
    # شرایط خودکار
    min_appointments_count = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('حداقل تعداد نوبت'))
    is_first_appointment = models.BooleanField(default=False, verbose_name=_('اولین نوبت'))
    is_weekend = models.BooleanField(default=False, verbose_name=_('آخر هفته'))
    specific_days = models.CharField(max_length=20, blank=True, verbose_name=_('روزهای خاص'))  # 0,1,2,3,4,5,6
    
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    
    class Meta:
        verbose_name = _('تخفیف خودکار')
        verbose_name_plural = _('تخفیفات خودکار')
    
    def __str__(self):
        return self.name
    
    def check_conditions(self, reservation, user):
        """بررسی شرایط تخفیف خودکار"""
        if not self.is_active:
            return False
        
        # بررسی اولین نوبت
        if self.is_first_appointment:
            previous_reservations = user.patient.reservations.exclude(id=reservation.id) if hasattr(user, 'patient') else []
            if previous_reservations.exists():
                return False
        
        # بررسی تعداد نوبت‌های قبلی
        if self.min_appointments_count:
            completed_appointments = user.patient.reservations.filter(status='completed').count() if hasattr(user, 'patient') else 0
            if completed_appointments < self.min_appointments_count:
                return False
        
        # بررسی روز هفته
        if self.specific_days:
            allowed_days = [int(d) for d in self.specific_days.split(',')]
            reservation_day = reservation.day.date.weekday()
            if reservation_day not in allowed_days:
                return False
        
        # بررسی آخر هفته
        if self.is_weekend:
            reservation_day = reservation.day.date.weekday()
            if reservation_day not in [4, 5]:  # پنج‌شنبه و جمعه
                return False
        
        return True


class DiscountReport(models.Model):
    """گزارش تخفیفات"""
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE, related_name='reports', verbose_name=_('تخفیف'))
    period_start = jmodels.jDateField(verbose_name=_('شروع دوره'))
    period_end = jmodels.jDateField(verbose_name=_('پایان دوره'))
    
    total_usage_count = models.PositiveIntegerField(default=0, verbose_name=_('تعداد کل استفاده'))
    total_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_('مبلغ کل تخفیف'))
    total_revenue_impact = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_('تأثیر بر درآمد'))
    
    generated_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('تاریخ تولید گزارش'))
    
    class Meta:
        verbose_name = _('گزارش تخفیف')
        verbose_name_plural = _('گزارش‌های تخفیف')
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"گزارش {self.discount.title} - {self.period_start} تا {self.period_end}" 