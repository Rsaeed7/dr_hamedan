from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django_jalali.db import models as jmodels
from decimal import Decimal
from django.utils import timezone
# from django.contrib.auth.models import User
from user.models import User


class Wallet(models.Model):
    """کیف پول کاربر"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet', verbose_name=_('کاربر'))
    balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('موجودی')
    )
    
    # موجودی در انتظار (برای پزشکان)
    pending_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('موجودی در انتظار')
    )
    
    # موجودی مسدود شده
    frozen_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('موجودی مسدود')
    )
    
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    
    class Meta:
        verbose_name = _('کیف پول')
        verbose_name_plural = _('کیف‌ پول‌ها')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.balance} تومان"
    
    def get_total_balance(self):
        """محاسبه موجودی کل"""
        return self.balance + self.pending_balance + self.frozen_balance
    
    def can_withdraw(self, amount):
        """بررسی امکان برداشت"""
        return self.balance >= amount and self.is_active
    
    def add_balance(self, amount, transaction_type='deposit'):
        """افزودن موجودی"""
        if amount > 0:
            if transaction_type == 'pending':
                self.pending_balance += amount
            else:
                self.balance += amount
            self.save()
            return True
        return False
    
    def subtract_balance(self, amount, from_pending=False):
        """کسر موجودی"""
        if from_pending:
            if self.pending_balance >= amount:
                self.pending_balance -= amount
                self.save()
                return True
        else:
            if self.balance >= amount:
                self.balance -= amount
                self.save()
                return True
        return False
    
    def freeze_balance(self, amount):
        """مسدود کردن موجودی"""
        if self.balance >= amount:
            self.balance -= amount
            self.frozen_balance += amount
            self.save()
            return True
        return False
    
    def unfreeze_balance(self, amount):
        """آزاد کردن موجودی مسدود"""
        if self.frozen_balance >= amount:
            self.frozen_balance -= amount
            self.balance += amount
            self.save()
            return True
        return False
    
    def move_pending_to_balance(self, amount=None):
        """انتقال موجودی در انتظار به موجودی اصلی"""
        if amount is None:
            amount = self.pending_balance
        
        if self.pending_balance >= amount:
            self.pending_balance -= amount
            self.balance += amount
            self.save()
            return True
        return False


class PaymentGateway(models.Model):
    """درگاه پرداخت"""
    name = models.CharField(max_length=100, verbose_name=_('نام درگاه'))
    code = models.CharField(max_length=50, unique=True, verbose_name=_('کد درگاه'))
    api_key = models.CharField(max_length=200, verbose_name=_('کلید API'))
    merchant_id = models.CharField(max_length=100, verbose_name=_('شناسه پذیرنده'))
    gateway_url = models.URLField(verbose_name=_('آدرس درگاه'))
    verify_url = models.URLField(verbose_name=_('آدرس تایید'))
    
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    min_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('1000'),
        verbose_name=_('حداقل مبلغ')
    )
    max_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('50000000'),
        verbose_name=_('حداکثر مبلغ')
    )
    
    commission_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('درصد کمیسیون')
    )
    
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    
    class Meta:
        verbose_name = _('درگاه پرداخت')
        verbose_name_plural = _('درگاه‌های پرداخت')
    
    def __str__(self):
        return self.name
    
    def calculate_commission(self, amount):
        """محاسبه کمیسیون"""
        return amount * (self.commission_percentage / Decimal('100'))


class Transaction(models.Model):
    """تراکنش"""
    TRANSACTION_TYPES = (
        ('payment', 'پرداخت'),
        ('refund', 'بازگشت وجه'),
        ('deposit', 'واریز'),
        ('withdrawal', 'برداشت'),
        ('commission', 'کمیسیون'),
        ('penalty', 'جریمه'),
        ('bonus', 'پاداش'),
        ('transfer', 'انتقال'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'در انتظار'),
        ('processing', 'در حال پردازش'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
        ('cancelled', 'لغو شده'),
        ('expired', 'منقضی شده'),
    )
    
    PAYMENT_METHODS = (
        ('gateway', 'درگاه پرداخت'),
        ('wallet', 'کیف پول'),
        ('card', 'کارت بانکی'),
        ('cash', 'نقدی'),
        ('transfer', 'انتقال بانکی'),
    )
    
    # اطلاعات اصلی
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions', verbose_name=_('کاربر'))
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions', verbose_name=_('کیف پول'))
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_('مبلغ'))
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, verbose_name=_('نوع تراکنش'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_('وضعیت'))
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='gateway', verbose_name=_('روش پرداخت'))
    
    # اطلاعات پرداخت
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('درگاه پرداخت'))
    reference_id = models.CharField(max_length=100, blank=True, verbose_name=_('شماره مرجع'))
    tracking_code = models.CharField(max_length=100, blank=True, verbose_name=_('کد پیگیری'))
    authority = models.CharField(max_length=100, blank=True, verbose_name=_('کد Authority'))
    
    # کمیسیون و هزینه‌ها
    commission_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('مبلغ کمیسیون')
    )
    fee_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('هزینه تراکنش')
    )
    net_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name=_('مبلغ خالص')
    )
    
    # روابط
    related_transaction = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='related_transactions', verbose_name=_('تراکنش مرتبط')
    )
    
    # اطلاعات اضافی
    description = models.TextField(blank=True, verbose_name=_('توضیحات'))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_('اطلاعات اضافی'))
    
    # تاریخ‌ها
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    processed_at = jmodels.jDateTimeField(null=True, blank=True, verbose_name=_('تاریخ پردازش'))
    expires_at = jmodels.jDateTimeField(null=True, blank=True, verbose_name=_('تاریخ انقضا'))
    
    class Meta:
        verbose_name = _('تراکنش')
        verbose_name_plural = _('تراکنش‌ها')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['reference_id']),
            models.Index(fields=['tracking_code']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_transaction_type_display()} - {self.amount} تومان"
    
    def save(self, *args, **kwargs):
        # محاسبه مبلغ خالص
        if not self.net_amount:
            self.net_amount = self.amount - self.commission_amount - self.fee_amount
        
        # تنظیم کیف پول اگر تنظیم نشده
        if not self.wallet_id and self.user_id:
            wallet, created = Wallet.objects.get_or_create(user=self.user)
            self.wallet = wallet
        
        super().save(*args, **kwargs)
    
    def is_successful(self):
        """بررسی موفقیت تراکنش"""
        return self.status == 'completed'
    
    def is_pending(self):
        """بررسی در انتظار بودن تراکنش"""
        return self.status in ['pending', 'processing']
    
    def can_be_refunded(self):
        """بررسی امکان بازگشت وجه"""
        return (
            self.status == 'completed' and
            self.transaction_type == 'payment' and
            not self.related_transactions.filter(transaction_type='refund').exists()
        )
    
    def mark_as_completed(self):
        """تکمیل تراکنش"""
        if self.status in ['pending', 'processing']:
            self.status = 'completed'
            self.processed_at = timezone.now()
            
            # اعمال تغییرات در کیف پول
            if self.transaction_type in ['deposit', 'refund', 'bonus']:
                self.wallet.add_balance(self.net_amount)
            elif self.transaction_type in ['withdrawal', 'payment', 'commission', 'penalty']:
                self.wallet.subtract_balance(self.net_amount)
            
            self.save()
            return True
        return False
    
    def mark_as_failed(self, reason=""):
        """شکست تراکنش"""
        if self.status in ['pending', 'processing']:
            self.status = 'failed'
            self.processed_at = timezone.now()
            if reason:
                self.metadata['failure_reason'] = reason
            self.save()
            return True
        return False
    
    def create_refund(self, amount=None, reason=""):
        """ایجاد تراکنش بازگشت وجه"""
        if not self.can_be_refunded():
            return None
        
        if amount is None:
            amount = self.net_amount
        
        refund_transaction = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            amount=amount,
            transaction_type='refund',
            status='completed',
            related_transaction=self,
            description=f"بازگشت وجه تراکنش {self.id}" + (f" - {reason}" if reason else ""),
            metadata={'original_transaction_id': self.id}
        )
        
        # اعمال در کیف پول
        self.wallet.add_balance(amount)
        
        return refund_transaction
