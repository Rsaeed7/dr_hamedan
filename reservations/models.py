from django.db import models
from django_jalali.db import models as jmodels
from patients.models import PatientsFile
from doctors.models import Doctor


class ReservationDay(models.Model):
    date = jmodels.jDateField(verbose_name='تاریخ')
    published = models.BooleanField(default=True, verbose_name='منتشر شده')
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    
    def __str__(self):
        return f"{self.date} - {'Published' if self.published else 'Unpublished'}"
    
    class Meta:
        verbose_name = 'روز رزرو'
        verbose_name_plural = 'روزهای رزرو'

class Reservation(models.Model):
    STATUS_CHOICES = (
        ('available', 'آزاد'),  # نوبت آزاد برای رزرو
        ('pending', 'در انتظار'),
        ('confirmed', 'تایید شده'),
        ('completed', 'تکمیل شده'),
        ('cancelled', 'لغو شده'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'در انتظار'),
        ('paid', 'پرداخت شده'),
        ('failed', 'ناموفق'),
        ('refunded', 'بازگشت وجه'),
    )
    
    day = models.ForeignKey(ReservationDay, on_delete=models.CASCADE, related_name='reservations', verbose_name='روز')
    patient = models.ForeignKey(PatientsFile, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations', verbose_name='بیمار')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='reservations', verbose_name='پزشک')
    time = models.TimeField(verbose_name='زمان')
    phone = models.CharField(max_length=20, verbose_name='شماره تلفن', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name='وضعیت')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name='وضعیت پرداخت')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='مبلغ')
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    transaction = models.ForeignKey('wallet.Transaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations', verbose_name='تراکنش')
    payment_request = models.ForeignKey('payments.PaymentRequest', on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations', verbose_name='درخواست پرداخت')
    notes = models.TextField(blank=True, null=True, verbose_name='یادداشت‌ها')
    
    # اطلاعات اضافی برای نوبت‌های رزرو شده
    patient_name = models.CharField(max_length=100, verbose_name='نام بیمار', blank=True)
    patient_national_id = models.CharField(max_length=20, verbose_name='کد ملی بیمار', blank=True)
    patient_email = models.EmailField(verbose_name='ایمیل بیمار', blank=True)
    
    def __str__(self):
        if self.status == 'available':
            return f"{self.doctor} - {self.day.date} {self.time} (آزاد)"
        patient_name = self.patient_name or (self.patient.name if self.patient else "Guest")
        return f"{patient_name} - {self.doctor} - {self.day.date} {self.time}"
    
    def is_available(self):
        """بررسی آزاد بودن نوبت"""
        return self.status == 'available'
    
    def book_appointment(self, patient_data, user=None, payment_method='wallet'):
        """رزرو نوبت آزاد"""
        if not self.is_available():
            return False, "این نوبت دیگر آزاد نیست"
        
        # Check if user is authenticated
        if not user or not user.is_authenticated:
            return False, "برای رزرو نوبت باید وارد شوید"
        
        # Import here to avoid circular imports
        from wallet.models import Wallet, Transaction
        from django.db import transaction as db_transaction
        
        # Get or create user's wallet
        wallet, created = Wallet.objects.get_or_create(user=user)
        
        # Check if user has sufficient balance for wallet payment
        appointment_fee = self.amount
        if payment_method == 'wallet':
            if not wallet.can_withdraw(appointment_fee):
                available_balance = wallet.balance
                return False, f"موجودی کیف پول کافی نیست. موجودی فعلی: {available_balance:,} تومان - مبلغ مورد نیاز: {appointment_fee:,} تومان. لطفاً کیف پول خود را شارژ کنید یا از پرداخت مستقیم استفاده کنید."
        
        try:
            with db_transaction.atomic():
                if payment_method == 'wallet':
                    # Deduct amount from wallet
                    if not wallet.subtract_balance(appointment_fee):
                        return False, "خطا در کسر مبلغ از کیف پول. لطفاً دوباره تلاش کنید."
                    
                    # Create payment transaction
                    payment_transaction = Transaction.objects.create(
                        user=user,
                        wallet=wallet,
                        amount=appointment_fee,
                        transaction_type='payment',
                        payment_method='wallet',
                        status='completed',
                        description=f'پرداخت نوبت پزشک {self.doctor} - {self.day.date} {self.time}',
                        metadata={
                            'doctor_id': self.doctor.id,
                            'doctor_name': str(self.doctor),
                            'appointment_date': str(self.day.date),
                            'appointment_time': str(self.time)
                        }
                    )
                    
                    # Update appointment details
                    self.patient_name = patient_data['name']
                    self.phone = patient_data['phone']
                    self.patient_national_id = patient_data.get('national_id', '')
                    self.patient_email = patient_data.get('email', '')
                    self.notes = patient_data.get('notes', '')
                    self.status = 'confirmed'  # Directly confirmed since payment is made
                    self.payment_status = 'paid'
                    self.transaction = payment_transaction
                    
                elif payment_method == 'direct':
                    # For direct payment, set status to pending and payment_status to pending
                    self.patient_name = patient_data['name']
                    self.phone = patient_data['phone']
                    self.patient_national_id = patient_data.get('national_id', '')
                    self.patient_email = patient_data.get('email', '')
                    self.notes = patient_data.get('notes', '')
                    self.status = 'pending'  # Pending until payment is completed
                    self.payment_status = 'pending'
                
                # Create or link patient file
                from patients.models import PatientsFile
                patient, created = PatientsFile.objects.get_or_create(
                    user=user,
                    defaults={
                        'phone': patient_data['phone'],
                        'email': user.email,
                        'national_id': patient_data.get('national_id', '')
                    }
                )
                self.patient = patient
                
                self.save()
                
                # Send confirmation notification only for wallet payments
                if payment_method == 'wallet' and self.patient and self.patient.user:
                    from utils.utils import send_notification
                    message = f"نوبت شما با دکتر {self.doctor.user.get_full_name()} در تاریخ {self.day.date} ساعت {self.time} تایید شد."
                    send_notification(
                        user=self.patient.user,
                        title='تایید نوبت',
                        message=message,
                        notification_type='success'
                    )
                
                if payment_method == 'wallet':
                    return True, f"نوبت با موفقیت رزرو و پرداخت شد. مبلغ {appointment_fee:,} تومان از کیف پول شما کسر گردید."
                else:
                    return True, f"نوبت با موفقیت رزرو شد. لطفاً پرداخت خود را تکمیل کنید."
                
        except Exception as e:
            return False, f"خطا در پردازش پرداخت: {str(e)}"

    def book_with_direct_payment(self, patient_data, user=None):
        """رزرو نوبت با پرداخت مستقیم"""
        return self.book_appointment(patient_data, user, payment_method='direct')
    
    def confirm_appointment(self):
        """Confirm this appointment"""
        if self.status == 'pending' and self.payment_status == 'paid':
            self.status = 'confirmed'
            self.save()
            
            # Send confirmation notification
            if self.patient and self.patient.user:
                from utils.utils import send_notification
                message = f"نوبت شما با دکتر {self.doctor.user.get_full_name()} در تاریخ {self.day.date} ساعت {self.time} تایید شد."
                send_notification(
                    user=self.patient.user,
                    title='تایید نوبت',
                    message=message,
                    notification_type='success'
                )
            return True
        return False
    
    def cancel_appointment(self, refund=True):
        """Cancel this appointment with optional refund"""
        if self.status in ['pending', 'confirmed']:
            # اگر نوبت رزرو شده بود، به حالت آزاد برگردان
            if self.status in ['pending', 'confirmed']:
                # Store patient info for notification before clearing
                patient_user = self.patient.user if self.patient else None
                doctor_name = self.doctor.user.get_full_name()
                appointment_date = self.day.date
                appointment_time = self.time
                
                self.status = 'available'
                self.patient = None
                self.patient_name = ''
                self.phone = ''
                self.patient_national_id = ''
                self.patient_email = ''
                self.notes = ''
                self.payment_status = 'pending'
                
                # Handle refund if requested and payment was made
                if refund and self.payment_status == 'paid':
                    self.payment_status = 'refunded'
                    
                    # Process refund in wallet app
                    if self.transaction:
                        from wallet.models import Transaction
                        Transaction.objects.create(
                            user=self.transaction.user,
                            amount=self.amount,
                            transaction_type='refund',
                            related_transaction=self.transaction,
                            status='completed',
                            description=f"Refund for cancelled appointment - {self}"
                        )
            
            self.save()
            
            # Send cancellation notification
            if patient_user:
                from utils.utils import send_notification
                message = f"نوبت شما با دکتر {doctor_name} در تاریخ {appointment_date} ساعت {appointment_time} لغو شد."
                send_notification(
                    user=patient_user,
                    title='لغو نوبت',
                    message=message,
                    notification_type='warning'
                )
            return True
        return False
    
    def complete_appointment(self):
        """Mark appointment as completed"""
        if self.status == 'confirmed' and self.payment_status == 'paid':
            self.status = 'completed'
            self.save()
            
            # Send completion notification
            if self.patient and self.patient.user:
                from utils.utils import send_notification
                message = f"نوبت شما با دکتر {self.doctor.user.get_full_name()} در تاریخ {self.day.date} ساعت {self.time} تکمیل شد. لطفاً نظر خود را درباره کیفیت خدمات ارائه دهید."
                send_notification(
                    user=self.patient.user,
                    title='تکمیل نوبت',
                    message=message,
                    notification_type='success'
                )
            return True
        return False

    class Meta:
        unique_together = ('day', 'doctor', 'time')
        verbose_name = 'رزرو'
        verbose_name_plural = 'رزروها'
        indexes = [
            models.Index(fields=['doctor', 'status']),
            models.Index(fields=['day', 'status']),
        ]
