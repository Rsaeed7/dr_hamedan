import os
import uuid
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_jalali.db import models as jmodels
from django.utils import timezone
from user.models import User
from wallet.models import Wallet, Transaction


class PaymentGateway(models.Model):
    """درگاه پرداخت"""
    GATEWAY_TYPES = (
        ('zarinpal', 'زرین‌پال'),
        ('mellat', 'ملت'),
        ('parsian', 'پارسیان'),
        ('saman', 'سامان'),
        ('custom', 'سفارشی'),
    )
    
    name = models.CharField(max_length=100, verbose_name=_('نام درگاه'))
    gateway_type = models.CharField(max_length=20, choices=GATEWAY_TYPES, verbose_name=_('نوع درگاه'))
    merchant_id = models.CharField(max_length=200, verbose_name=_('شناسه پذیرنده'))
    api_key = models.CharField(max_length=200, blank=True, verbose_name=_('کلید API'))
    
    # ZarinPal specific settings
    zp_api_request = models.URLField(blank=True, verbose_name=_('آدرس درخواست'))
    zp_api_verify = models.URLField(blank=True, verbose_name=_('آدرس تایید'))
    zp_api_startpay = models.URLField(blank=True, verbose_name=_('آدرس شروع پرداخت'))
    
    # General settings
    callback_url = models.URLField(verbose_name=_('آدرس بازگشت'))
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    is_sandbox = models.BooleanField(default=True, verbose_name=_('محیط تست'))
    
    # Limits
    min_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('1000'),
        verbose_name=_('حداقل مبلغ')
    )
    max_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('50000000'),
        verbose_name=_('حداکثر مبلغ')
    )
    
    # Commission
    commission_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('درصد کمیسیون')
    )
    fixed_commission = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('کمیسیون ثابت')
    )
    
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    
    class Meta:
        verbose_name = _('درگاه پرداخت')
        verbose_name_plural = _('درگاه‌های پرداخت')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_gateway_type_display()})"
    
    def get_api_urls(self):
        """دریافت آدرس‌های API بر اساس نوع درگاه"""
        if self.gateway_type == 'zarinpal':
            if self.is_sandbox:
                return {
                    'request': 'https://sandbox.zarinpal.com/pg/v4/payment/request.json',
                    'verify': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
                    'startpay': 'https://sandbox.zarinpal.com/pg/StartPay/{authority}'
                }
            else:
                return {
                    'request': 'https://api.zarinpal.com/pg/v4/payment/request.json',
                    'verify': 'https://api.zarinpal.com/pg/v4/payment/verify.json',
                    'startpay': 'https://www.zarinpal.com/pg/StartPay/{authority}'
                }
        return {}
    
    def calculate_commission(self, amount):
        """محاسبه کمیسیون"""
        commission = self.fixed_commission
        commission += amount * (self.commission_percentage / Decimal('100'))
        return commission


class PaymentRequest(models.Model):
    """درخواست پرداخت"""
    STATUS_CHOICES = (
        ('pending', 'در انتظار'),
        ('processing', 'در حال پردازش'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
        ('cancelled', 'لغو شده'),
        ('expired', 'منقضی شده'),
    )
    
    # اطلاعات اصلی
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_requests', verbose_name=_('کاربر'))
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='payment_requests', verbose_name=_('کیف پول'))
    
    # اطلاعات پرداخت
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_('مبلغ'))
    description = models.TextField(verbose_name=_('توضیحات'))
    
    # درگاه پرداخت
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.CASCADE, verbose_name=_('درگاه پرداخت'))
    
    # اطلاعات درگاه
    authority = models.CharField(max_length=100, blank=True, verbose_name=_('کد Authority'))
    ref_id = models.CharField(max_length=100, blank=True, verbose_name=_('کد پیگیری'))
    card_pan = models.CharField(max_length=20, blank=True, verbose_name=_('شماره کارت'))
    
    # وضعیت
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_('وضعیت'))
    
    # اطلاعات اضافی
    callback_url = models.URLField(blank=True, verbose_name=_('آدرس بازگشت'))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_('اطلاعات اضافی'))
    
    # تراکنش مرتبط
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_requests', verbose_name=_('تراکنش'))
    
    # تاریخ‌ها
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    expires_at = jmodels.jDateTimeField(null=True, blank=True, verbose_name=_('تاریخ انقضا'))
    completed_at = jmodels.jDateTimeField(null=True, blank=True, verbose_name=_('تاریخ تکمیل'))
    
    class Meta:
        verbose_name = _('درخواست پرداخت')
        verbose_name_plural = _('درخواست‌های پرداخت')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['authority']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.amount} تومان - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # تنظیم تاریخ انقضا (15 دقیقه)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=15)
        
        # تنظیم کیف پول اگر تنظیم نشده
        if not self.wallet_id and self.user_id:
            wallet, created = Wallet.objects.get_or_create(user=self.user)
            self.wallet = wallet
        
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """بررسی انقضای درخواست"""
        return self.expires_at and timezone.now() > self.expires_at
    
    def can_be_processed(self):
        """بررسی امکان پردازش"""
        return self.status in ['pending', 'processing'] and not self.is_expired()
    
    def mark_as_completed(self, ref_id=None, card_pan=None):
        """تکمیل پرداخت"""
        if self.can_be_processed():
            self.status = 'completed'
            self.completed_at = timezone.now()
            if ref_id:
                self.ref_id = ref_id
            if card_pan:
                self.card_pan = card_pan
            self.save()
            
            # ایجاد تراکنش در کیف پول
            if not self.transaction:
                transaction = Transaction.objects.create(
                    user=self.user,
                    wallet=self.wallet,
                    amount=self.amount,
                    transaction_type='deposit',
                    payment_method='gateway',
                    gateway=self.gateway,
                    reference_id=ref_id,
                    tracking_code=str(uuid.uuid4())[:12].upper(),
                    description=self.description,
                    status='completed',
                    processed_at=timezone.now(),
                    metadata={
                        'payment_request_id': self.id,
                        'authority': self.authority,
                        'card_pan': card_pan
                    }
                )
                self.transaction = transaction
                self.save()
                
                # اضافه کردن موجودی به کیف پول
                self.wallet.add_balance(self.amount)
            
            return True
        return False
    
    def mark_as_failed(self, reason=""):
        """شکست پرداخت"""
        if self.can_be_processed():
            self.status = 'failed'
            self.completed_at = timezone.now()
            if reason:
                self.metadata['failure_reason'] = reason
            self.save()
            return True
        return False


class PaymentLog(models.Model):
    """لاگ پرداخت‌ها"""
    LOG_TYPES = (
        ('request', 'درخواست'),
        ('callback', 'بازگشت'),
        ('verify', 'تایید'),
        ('error', 'خطا'),
    )
    
    payment_request = models.ForeignKey(PaymentRequest, on_delete=models.CASCADE, related_name='logs', verbose_name=_('درخواست پرداخت'))
    log_type = models.CharField(max_length=20, choices=LOG_TYPES, verbose_name=_('نوع لاگ'))
    message = models.TextField(verbose_name=_('پیام'))
    data = models.JSONField(default=dict, blank=True, verbose_name=_('داده‌ها'))
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    
    class Meta:
        verbose_name = _('لاگ پرداخت')
        verbose_name_plural = _('لاگ‌های پرداخت')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.payment_request} - {self.get_log_type_display()} - {self.created_at}" 