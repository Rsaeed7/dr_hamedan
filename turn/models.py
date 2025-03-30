from django_jalali.db import models as jmodels
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


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
        date = f"{DATE_DAY[dateList[2]]} {DATE_MONTH[dateList[1]]}"
        return str(date)



class Patients_File(models.Model):
    name = models.CharField(null=True,blank=True, verbose_name=_('نام بیمار'), max_length=100)
    phone = models.CharField(max_length=11, blank=True, verbose_name=_('شماره تلفن'))
    meli_code = models.CharField(max_length=11, blank=True, verbose_name=_('کد ملی'))
    involvement = models.CharField(max_length=200, blank=True, verbose_name=_('بیماری'))
    description = models.TextField(null=True,blank=True, verbose_name=_('توضیحات'))

    class Meta:
        verbose_name = _('پرونده بیمار')
        verbose_name_plural = _('پرونده بیماران')

    def __str__(self):
        return f'{self.name}'

class Reservation(models.Model):
    day = models.ForeignKey(Reservation_Day, on_delete=models.CASCADE, verbose_name=_('تاریخ'), related_name='reservations')
    patient = models.ForeignKey(Patients_File, on_delete=models.CASCADE, verbose_name=_('بیمار'), related_name='patient',null=True, blank=True)
    phone = models.CharField(max_length=11, blank=True, verbose_name=_('شماره تلفن'))
    time = models.TimeField(_('Time'))

    class Meta:
        verbose_name = _('نوبت')
        verbose_name_plural = _('نوبت ها')
        ordering = ('time',)
    
    def __str__(self):
        return f'{self.patient} - {self.time}'



