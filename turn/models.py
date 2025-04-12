from django_jalali.db import models as jmodels
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from wallet.models import Transaction


DATE_MONTH = {
    "01": "فروردین",
    "02": "اردیبهشت",
    "03": "خرداد",
    "04": "تیر",
    "05": "مرداد",
    "06": "شهریور",
    "07": "مهر",
    "08": "آبان",
    "09": "آذز",
    "10": "دی",
    "11": "بهمن",
    "12": "اسفند",
}


DATE_DAY = {
   '01':'۱' ,
   '02':'۲' ,
   '03':'۳' ,
   '04':'۴' ,
   '05':'۵' ,
   '06':'۶' ,
   '07':'۷' ,
   '08':'۸' ,
   '09':'۹' ,
   '10':'۱۰',
   '11': '۱۱',
   '12': '۱۲',
   '13': '۱۳',
   '14': '۱۴',
   '15': '۱۵',
   '16': '۱۶',
   '17': '۱۷',
   '18': '۱۸',
   '19': '۱۹',
   '20': '۲۰',
   '21':'۲۱',
   '22':'۲۲',
   '23': '۲۳',
   '24': '۲۴',
   '25': '۲۵',
   '26': '۲۶',
   '27': '۲۷',
   '28': '۲۸',
   '29': '۲۹',
   '30': '۳۰',
   '31': '۳۱',
}


class Reservation_Day(models.Model):
    date = jmodels.jDateField(_('تاریخ'))
    published = models.BooleanField(_('نوبت فعال'),default=True)
    class Meta:
        verbose_name = _('تاریخ نوبت')
        verbose_name_plural = _('تاریخ نوبت ها')
        ordering = ('date',)
    def __str__(self):
        return " %s" % ( self.date)

    def dateformat(self):
        dateList = str(self.date).split("-")
        date = f"{DATE_DAY[dateList[2]]}"
        return str(date)



class Patients_File(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile', null=True, blank=True)
    name = models.CharField(null=True,blank=True, verbose_name=_('نام بیمار'), max_length=100)
    phone = models.CharField(max_length=11, blank=True, verbose_name=_('شماره تلفن'))
    meli_code = models.CharField(max_length=11, blank=True, verbose_name=_('کد ملی'))
    involvement = models.CharField(max_length=200, blank=True, verbose_name=_('بیماری'))
    description = models.TextField(null=True,blank=True, verbose_name=_('توضیحات'))
    birthdate = models.DateField(null=True, blank=True, verbose_name=_('تاریخ تولد'))
    
    class Meta:
        verbose_name = _('پرونده بیمار')
        verbose_name_plural = _('پرونده بیماران')

    def __str__(self):
        return f'{self.name}'


class Reservation(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, _('در انتظار')),
        (STATUS_CONFIRMED, _('تایید شده')),
        (STATUS_COMPLETED, _('تکمیل شده')),
        (STATUS_CANCELLED, _('لغو شده')),
    ]
    
    PAYMENT_PENDING = 'pending'
    PAYMENT_PAID = 'paid'
    PAYMENT_FAILED = 'failed'
    PAYMENT_REFUNDED = 'refunded'
    
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, _('در انتظار پرداخت')),
        (PAYMENT_PAID, _('پرداخت شده')),
        (PAYMENT_FAILED, _('ناموفق')),
        (PAYMENT_REFUNDED, _('بازگشت وجه')),
    ]
    
    day = models.ForeignKey(Reservation_Day, on_delete=models.CASCADE, verbose_name=_('تاریخ'), related_name='reservations')
    patient = models.ForeignKey(Patients_File, on_delete=models.CASCADE, verbose_name=_('بیمار'), related_name='patient_reservations', null=True, blank=True)
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, verbose_name=_('پزشک'), related_name='doctor_reservations', null=True)
    phone = models.CharField(max_length=11, blank=True, verbose_name=_('شماره تلفن'))
    time = models.TimeField(_('زمان'))
    status = models.CharField(_('وضعیت'), max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_status = models.CharField(_('وضعیت پرداخت'), max_length=20, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_PENDING)
    amount = models.DecimalField(_('مبلغ'), max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(_('تاریخ ایجاد'), default=timezone.now)
    updated_at = models.DateTimeField(_('تاریخ بروزرسانی'), auto_now=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('تراکنش'), related_name='reservations')
    notes = models.TextField(_('یادداشت ها'), blank=True, null=True)

    class Meta:
        verbose_name = _('نوبت')
        verbose_name_plural = _('نوبت ها')
        ordering = ('time',)
    
    def __str__(self):
        return f'{self.patient} - {self.doctor} - {self.day.date} {self.time}'
    
    def confirm_appointment(self):
        """Confirm an appointment after payment is successful"""
        self.status = self.STATUS_CONFIRMED
        self.payment_status = self.PAYMENT_PAID
        self.save()
        
    def cancel_appointment(self):
        """Cancel an appointment and handle refunds if needed"""
        self.status = self.STATUS_CANCELLED
        if self.payment_status == self.PAYMENT_PAID:
            self.payment_status = self.PAYMENT_REFUNDED
            # Handle refund logic here
        self.save()
        
    def complete_appointment(self):
        """Mark an appointment as completed after the visit"""
        self.status = self.STATUS_COMPLETED
        self.save()



