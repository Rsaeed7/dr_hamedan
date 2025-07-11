from django.db import models
from django.utils import timezone
from doctors.models import Doctor
from patients.models import PatientsFile as Patient
from user.models import User
from django_jalali.db import models as jmodels

class ChatRequest(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    FINISHED = 'finished'

    STATUS_CHOICES = [
        (PENDING, 'در انتظار تایید'),
        (APPROVED, 'تایید شده'),
        (REJECTED, 'رد شده'),
        (FINISHED, 'پایان یافته'),
    ]
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'در انتظار'),
        ('paid', 'پرداخت شده'),
        ('failed', 'ناموفق'),
        ('refunded', 'بازگشت وجه'),
    )

    patient = models.ForeignKey(Patient,unique=False, on_delete=models.CASCADE, related_name='chat_requests', verbose_name='بیمار')
    doctor = models.ForeignKey(Doctor,unique=False, on_delete=models.CASCADE, related_name='chat_requests', verbose_name='پزشک')
    disease_summary = models.TextField(verbose_name='خلاصه بیماری',blank=True,null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING, verbose_name='وضعیت')
    
    # Payment fields
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name='وضعیت پرداخت')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='مبلغ', default=0)
    transaction = models.ForeignKey('wallet.Transaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_requests', verbose_name='تراکنش')
    
    # Patient information for payment
    patient_name = models.CharField(max_length=100, verbose_name='نام بیمار', blank=True)
    patient_national_id = models.CharField(max_length=20, verbose_name='کد ملی بیمار', blank=True)
    phone = models.CharField(max_length=20, verbose_name='شماره تلفن', blank=True)
    
    created_at = jmodels.jDateTimeField(default=timezone.now, verbose_name='تاریخ ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'درخواست چت'
        verbose_name_plural = 'درخواست‌های چت'

    def __str__(self):
        return f"درخواست چت {self.id} - بیمار: {getattr(self.patient.user, 'name', 'نامشخص')}"
    
    def process_payment(self, user):
        """پردازش پرداخت برای درخواست چت"""
        # Import here to avoid circular imports
        from wallet.models import Wallet, Transaction
        from django.db import transaction as db_transaction
        
        # Get or create user's wallet
        wallet, created = Wallet.objects.get_or_create(user=user)
        
        # Check if user has sufficient balance
        consultation_fee = self.amount
        if not wallet.can_withdraw(consultation_fee):
            available_balance = wallet.balance
            return False, f"موجودی کیف پول کافی نیست. موجودی فعلی: {available_balance:,} تومان - مبلغ مورد نیاز: {consultation_fee:,} تومان. لطفاً کیف پول خود را شارژ کنید."
        
        try:
            with db_transaction.atomic():
                # Deduct amount from wallet
                if not wallet.subtract_balance(consultation_fee):
                    return False, "خطا در کسر مبلغ از کیف پول. لطفاً دوباره تلاش کنید."
                
                # Create payment transaction
                payment_transaction = Transaction.objects.create(
                    user=user,
                    wallet=wallet,
                    amount=consultation_fee,
                    transaction_type='payment',
                    payment_method='wallet',
                    status='completed',
                    description=f'پرداخت مشاوره آنلاین دکتر {self.doctor.user.get_full_name()}',
                    metadata={
                        'doctor_id': self.doctor.id,
                        'doctor_name': str(self.doctor),
                        'chat_request_id': self.id,
                        'consultation_type': 'online_chat'
                    }
                )
                
                # Update chat request
                self.payment_status = 'paid'
                self.transaction = payment_transaction
                self.save()
                
                return True, f"پرداخت با موفقیت انجام شد. مبلغ {consultation_fee:,} تومان از کیف پول شما کسر گردید."
                
        except Exception as e:
            return False, f"خطا در پردازش پرداخت: {str(e)}"


class ChatRoom(models.Model):
    request = models.OneToOneField(ChatRequest, on_delete=models.CASCADE, related_name='chat_room', verbose_name='درخواست مربوطه')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = jmodels.jDateTimeField(default=timezone.now, verbose_name='تاریخ ایجاد')
    last_activity = jmodels.jDateTimeField(default=timezone.now, verbose_name='آخرین فعالیت')

    class Meta:
        ordering = ['-last_activity']
        verbose_name = 'اتاق چت'
        verbose_name_plural = 'اتاق‌های چت'

    def __str__(self):
        return f"اتاق چت {self.id} - پزشک: {getattr(self.request.doctor.user, 'name', 'نامشخص')}"

class Message(models.Model):
    TEXT = 'text'
    IMAGE = 'image'
    FILE = 'file'
    AUDIO = 'audio'

    MESSAGE_TYPE_CHOICES = [
        (TEXT, 'متن'),
        (IMAGE, 'تصویر'),
        (FILE, 'فایل'),
        (AUDIO, 'صوت'),
    ]

    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='اتاق چت'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='فرستنده'
    )
    content = models.TextField(
        verbose_name='محتوا',
        blank=True,
        null=True
    )
    file = models.FileField(
        upload_to='chat/files/',
        blank=True,
        null=True,
        verbose_name='فایل'
    )
    audio = models.FileField(
        upload_to='chat/audio/',
        blank=True,
        null=True,
        verbose_name='صوت'
    )
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPE_CHOICES,
        default=TEXT,
        verbose_name='نوع پیام'
    )
    created_at = jmodels.jDateTimeField(
        default=timezone.now,
        verbose_name='تاریخ ارسال'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='خوانده شده'
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = 'پیام'
        verbose_name_plural = 'پیام‌ها'

    def __str__(self):
        return f"پیام {self.id} - {self.sender.name if self.sender else 'ناشناس'} - نوع: {self.message_type}"



class DoctorAvailability(models.Model):
    doctor = models.OneToOneField(
        Doctor,
        on_delete=models.CASCADE,
        related_name='availability',
        verbose_name='پزشک'
    )
    is_available = models.BooleanField(
        default=False,
        verbose_name='وضعیت دسترسی'
    )
    last_active = jmodels.jDateTimeField(
        auto_now=True,
        verbose_name='آخرین فعالیت'
    )

    class Meta:
        verbose_name = 'وضعیت دسترسی پزشک'
        verbose_name_plural = 'وضعیت دسترسی پزشکان'

    def __str__(self):
        return f"{self.doctor.user.name} - {'آنلاین' if self.is_available else 'آفلاین'}"