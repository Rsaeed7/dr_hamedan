from django.db import models
# from django.contrib.auth.models import User
from user.models import User
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('payment', 'پرداخت'),
        ('refund', 'بازگشت وجه'),
        ('deposit', 'واریز'),
        ('withdrawal', 'برداشت'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'در انتظار'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
        ('cancelled', 'لغو شده'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions', verbose_name='کاربر')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='مبلغ')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, verbose_name='نوع تراکنش')
    related_transaction = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='related_transactions', verbose_name='تراکنش مرتبط')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount} - {self.status}"

    class Meta:
        verbose_name = 'تراکنش'
        verbose_name_plural = 'تراکنش‌ها'
