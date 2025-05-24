# SMS Reminder System

یک سیستم جامع یادآوری پیامک برای پلتفرم رزرو نوبت دکتر ترن که امکان ارسال یادآوری‌های خودکار، تأیید و لغو نوبت‌ها را فراهم می‌کند.

## ویژگی‌های کلیدی

### 🔔 یادآوری‌های خودکار
- یادآوری 24 ساعته قبل از نوبت
- یادآوری 2 ساعته قبل از نوبت
- ارسال در ساعات کاری
- سیستم تلاش مجدد برای پیامک‌های ناموفق

### 📱 پیامک‌های فوری
- تأیید رزرو نوبت
- اطلاع‌رسانی لغو نوبت
- پیامک‌های سفارشی

### ⚙️ مدیریت پیشرفته
- تنظیمات قابل تغییر از پنل ادمین
- گزارش‌گیری دقیق
- لاگ کامل عملیات
- پاکسازی خودکار داده‌های قدیمی

## ساختار پروژه

```
sms_reminders/
├── models.py              # مدل‌های دیتابیس
├── admin.py               # رابط مدیریت
├── services.py            # سرویس‌های اصلی
├── management/
│   └── commands/
│       ├── process_sms_reminders.py    # پردازش یادآوری‌ها
│       ├── send_test_sms.py            # تست ارسال پیامک
│       ├── cleanup_old_reminders.py    # پاکسازی داده‌ها
│       └── sms_reminder_report.py      # گزارش‌گیری
├── migrations/            # مایگریشن‌های دیتابیس
└── README.md             # این فایل
```

## مدل‌های دیتابیس

### SMSReminderSettings
تنظیمات کلی سیستم یادآوری پیامک

```python
class SMSReminderSettings(models.Model):
    enabled = models.BooleanField(default=True)
    reminder_24h_enabled = models.BooleanField(default=True)
    reminder_2h_enabled = models.BooleanField(default=True)
    confirmation_sms_enabled = models.BooleanField(default=True)
    cancellation_sms_enabled = models.BooleanField(default=True)
    working_hours_start = models.TimeField(default='08:00')
    working_hours_end = models.TimeField(default='20:00')
    max_retry_attempts = models.PositiveIntegerField(default=3)
```

### SMSReminder
ذخیره اطلاعات هر یادآوری پیامک

```python
class SMSReminder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('sent', 'ارسال شده'),
        ('failed', 'ناموفق'),
        ('cancelled', 'لغو شده'),
    ]
    
    TYPE_CHOICES = [
        ('reminder_24h', 'یادآوری 24 ساعته'),
        ('reminder_2h', 'یادآوری 2 ساعته'),
        ('confirmation', 'تأیید نوبت'),
        ('cancellation', 'لغو نوبت'),
    ]
```

### SMSReminderTemplate
قالب‌های پیامک قابل تنظیم

### SMSLog
لاگ کامل ارسال پیامک‌ها

## نصب و راه‌اندازی

### 1. اضافه کردن به INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'sms_reminders',
]
```

### 2. اجرای مایگریشن‌ها

```bash
python manage.py makemigrations sms_reminders
python manage.py migrate
```

### 3. ایجاد تنظیمات اولیه

```bash
python manage.py shell
```

```python
from sms_reminders.models import SMSReminderSettings
SMSReminderSettings.objects.create()
```

## استفاده از سیستم

### ارسال یادآوری برای نوبت

```python
from sms_reminders.services import schedule_appointment_reminders
from reservations.models import Reservation

reservation = Reservation.objects.get(id=1)
reminders = schedule_appointment_reminders(reservation)
```

### ارسال تأیید نوبت

```python
from sms_reminders.services import send_confirmation_sms

confirmation = send_confirmation_sms(reservation)
```

### لغو یادآوری‌ها

```python
from sms_reminders.services import cancel_reminders_for_reservation

cancelled_count = cancel_reminders_for_reservation(reservation)
```

## دستورات مدیریتی

### پردازش یادآوری‌های در انتظار

```bash
# پردازش یادآوری‌های معوق
python manage.py process_sms_reminders

# پردازش + تلاش مجدد برای ناموفق‌ها
python manage.py process_sms_reminders --retry-failed

# حالت تست (بدون ارسال واقعی)
python manage.py process_sms_reminders --dry-run
```

### تست ارسال پیامک

```bash
# ارسال پیامک تست
python manage.py send_test_sms 09123456789

# پیامک سفارشی
python manage.py send_test_sms 09123456789 --message "پیام تست"
```

### پاکسازی داده‌های قدیمی

```bash
# پاک کردن یادآوری‌های بیش از 30 روز
python manage.py cleanup_old_reminders

# پاک کردن یادآوری‌های بیش از 7 روز
python manage.py cleanup_old_reminders --days 7

# نگه داشتن یادآوری‌های ناموفق
python manage.py cleanup_old_reminders --keep-failed

# حالت تست
python manage.py cleanup_old_reminders --dry-run
```

### گزارش‌گیری

```bash
# گزارش 7 روز گذشته
python manage.py sms_reminder_report

# گزارش 30 روز گذشته
python manage.py sms_reminder_report --days 30

# گزارش تفصیلی
python manage.py sms_reminder_report --detailed

# خروجی JSON
python manage.py sms_reminder_report --format json
```

## تنظیم Cron Jobs

برای اجرای خودکار سیستم، دستورات زیر را به crontab اضافه کنید:

```bash
# پردازش یادآوری‌ها هر 15 دقیقه
*/15 * * * * cd /path/to/project && python manage.py process_sms_reminders

# تلاش مجدد برای ناموفق‌ها هر ساعت
0 * * * * cd /path/to/project && python manage.py process_sms_reminders --retry-failed

# پاکسازی هفتگی
0 2 * * 0 cd /path/to/project && python manage.py cleanup_old_reminders

# گزارش روزانه
0 8 * * * cd /path/to/project && python manage.py sms_reminder_report --days 1
```

## تنظیمات پیشرفته

### تنظیم ساعات کاری

```python
# در پنل ادمین یا shell
settings = SMSReminderSettings.objects.first()
settings.working_hours_start = '09:00'
settings.working_hours_end = '18:00'
settings.save()
```

### تنظیم تعداد تلاش مجدد

```python
settings.max_retry_attempts = 5
settings.save()
```

### غیرفعال کردن انواع یادآوری

```python
settings.reminder_24h_enabled = False  # غیرفعال کردن یادآوری 24 ساعته
settings.confirmation_sms_enabled = False  # غیرفعال کردن تأیید
settings.save()
```

## قالب‌های پیامک

قالب‌های پیش‌فرض قابل تنظیم از پنل ادمین:

### یادآوری 24 ساعته
```
سلام {patient_name}
یادآوری: فردا راس ساعت {appointment_time} نوبت شما نزد {doctor_name} می‌باشد.
آدرس: {clinic_address}
```

### یادآوری 2 ساعته
```
سلام {patient_name}
یادآوری: 2 ساعت دیگر نوبت شما نزد {doctor_name} می‌باشد.
```

### تأیید نوبت
```
نوبت شما با موفقیت ثبت شد.
تاریخ: {appointment_date}
ساعت: {appointment_time}
دکتر: {doctor_name}
```

## مونیتورینگ و عیب‌یابی

### بررسی وضعیت سیستم

```python
from sms_reminders.models import SMSReminderSettings, SMSReminder

# بررسی تنظیمات
settings = SMSReminderSettings.objects.first()
print(f"SMS System Enabled: {settings.enabled}")

# بررسی یادآوری‌های معوق
pending = SMSReminder.objects.filter(status='pending').count()
print(f"Pending reminders: {pending}")

# بررسی یادآوری‌های ناموفق
failed = SMSReminder.objects.filter(status='failed').count()
print(f"Failed reminders: {failed}")
```

### لاگ‌های سیستم

```python
import logging

# فعال کردن لاگ‌های SMS
logger = logging.getLogger('sms_reminders')
logger.setLevel(logging.INFO)
```

## بهینه‌سازی عملکرد

### ایندکس‌های دیتابیس
```python
# در models.py
class SMSReminder(models.Model):
    # ...
    class Meta:
        indexes = [
            models.Index(fields=['status', 'scheduled_time']),
            models.Index(fields=['reservation']),
            models.Index(fields=['created_at']),
        ]
```

### تنظیمات Celery (اختیاری)
برای پردازش ناهمزمان:

```python
# tasks.py
from celery import shared_task
from .services import process_pending_reminders

@shared_task
def process_sms_reminders():
    return process_pending_reminders()
```

## امنیت

### محافظت از شماره تلفن
- رمزنگاری شماره‌های تلفن در دیتابیس
- اعتبارسنجی فرمت شماره تلفن
- محدودیت نرخ ارسال

### کنترل دسترسی
- تنها کاربران مجاز می‌توانند تنظیمات را تغییر دهند
- لاگ کامل تغییرات

## پشتیبانی و توسعه

### گزارش مشکلات
- بررسی لاگ‌های سیستم
- استفاده از دستور `sms_reminder_report` برای تحلیل
- بررسی تنظیمات SMS provider

### توسعه‌های آینده
- پشتیبانی از چندین SMS provider
- یادآوری‌های شخصی‌سازی شده
- ادغام با سیستم‌های پیام‌رسان
- پشتیبانی از قالب‌های HTML

## مجوز

این سیستم بخشی از پروژه دکتر ترن است و تحت مجوز MIT منتشر شده است. 