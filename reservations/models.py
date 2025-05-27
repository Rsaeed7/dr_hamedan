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
    
    def book_appointment(self, patient_data, user=None):
        """رزرو نوبت آزاد"""
        if not self.is_available():
            return False, "این نوبت دیگر آزاد نیست"
        
        # بروزرسانی اطلاعات نوبت
        self.patient_name = patient_data['name']
        self.phone = patient_data['phone']
        self.patient_national_id = patient_data.get('national_id', '')
        self.patient_email = patient_data.get('email', '')
        self.notes = patient_data.get('notes', '')
        self.status = 'pending'
        
        # اتصال به فایل بیمار اگر کاربر وارد شده باشد
        if user and user.is_authenticated:
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
        return True, "نوبت با موفقیت رزرو شد"
    
    def confirm_appointment(self):
        """Confirm this appointment"""
        if self.status == 'pending' and self.payment_status == 'paid':
            self.status = 'confirmed'
            self.save()
            # TODO: Send confirmation email/notification
            return True
        return False
    
    def cancel_appointment(self, refund=True):
        """Cancel this appointment with optional refund"""
        if self.status in ['pending', 'confirmed']:
            # اگر نوبت رزرو شده بود، به حالت آزاد برگردان
            if self.status in ['pending', 'confirmed']:
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
            # TODO: Send cancellation email/notification
            return True
        return False
    
    def complete_appointment(self):
        """Mark appointment as completed"""
        if self.status == 'confirmed' and self.payment_status == 'paid':
            self.status = 'completed'
            self.save()
            # TODO: Send completion email/notification
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
