# سیستم تخفیفات Dr. Turn

سیستم جامع مدیریت تخفیفات برای پلتفرم رزرو نوبت پزشک Dr. Turn

## ویژگی‌های اصلی

### 🎯 انواع تخفیف
- **تخفیف درصدی**: تخفیف بر اساس درصد مبلغ
- **تخفیف مبلغ ثابت**: تخفیف با مبلغ مشخص
- **یکی بخر یکی بگیر**: تخفیف ویژه (آماده توسعه)

### 🎫 کدهای تخفیف
- ایجاد کدهای تخفیف منحصر به فرد
- مدیریت تاریخ انقضا
- محدودیت تعداد استفاده
- ردیابی استفاده کاربران

### 🤖 تخفیفات خودکار
- تخفیف اولین نوبت
- تخفیف آخر هفته
- تخفیف روزهای خاص
- شرایط قابل تنظیم

### 📊 گزارش‌گیری
- آمار استفاده از تخفیفات
- محاسبه تأثیر بر درآمد
- گزارش‌های دوره‌ای

## نصب و راه‌اندازی

### 1. اضافه کردن به INSTALLED_APPS

```python
INSTALLED_APPS = [
    # ... سایر اپلیکیشن‌ها
    'discounts',
]
```

### 2. اضافه کردن URLها

```python
# urls.py
urlpatterns = [
    # ... سایر URLها
    path('discounts/', include('discounts.urls')),
]
```

### 3. اجرای Migration

```bash
python manage.py makemigrations discounts
python manage.py migrate
```

### 4. ایجاد داده‌های نمونه

```bash
python manage.py create_sample_discounts
```

## مدل‌های اصلی

### DiscountType (نوع تخفیف)
```python
- name: نام نوع تخفیف
- type: نوع (percentage, fixed_amount, buy_one_get_one)
- description: توضیحات
- is_active: وضعیت فعال/غیرفعال
```

### Discount (تخفیف)
```python
- title: عنوان تخفیف
- description: توضیحات
- discount_type: نوع تخفیف
- percentage: درصد تخفیف (برای تخفیف درصدی)
- fixed_amount: مبلغ ثابت (برای تخفیف مبلغ ثابت)
- applicable_to: قابل اعمال برای (all, doctor, specialization, clinic, first_time, returning)
- min_amount: حداقل مبلغ سفارش
- max_discount_amount: حداکثر مبلغ تخفیف
- start_date: تاریخ شروع
- end_date: تاریخ پایان
- usage_limit: محدودیت استفاده کل
- usage_limit_per_user: محدودیت استفاده هر کاربر
- status: وضعیت (active, inactive, expired, used_up)
```

### CouponCode (کد تخفیف)
```python
- code: کد تخفیف
- discount: تخفیف مرتبط
- is_active: وضعیت فعال/غیرفعال
```

### AutomaticDiscount (تخفیف خودکار)
```python
- name: نام
- discount: تخفیف مرتبط
- min_appointments_count: حداقل تعداد نوبت
- is_first_appointment: اولین نوبت
- is_weekend: آخر هفته
- specific_days: روزهای خاص
```

### DiscountUsage (استفاده از تخفیف)
```python
- discount: تخفیف
- user: کاربر
- reservation: رزرو
- coupon_code: کد تخفیف (اختیاری)
- original_amount: مبلغ اصلی
- discount_amount: مبلغ تخفیف
- final_amount: مبلغ نهایی
```

### DiscountReport (گزارش تخفیف)
```python
- discount: تخفیف
- period_start: شروع دوره
- period_end: پایان دوره
- total_usage_count: تعداد کل استفاده
- total_discount_amount: مبلغ کل تخفیف
- total_revenue_impact: تأثیر بر درآمد
```

## API Endpoints

### لیست تخفیفات
```
GET /discounts/
```

### جزئیات تخفیف
```
GET /discounts/<id>/
```

### اعمال کد تخفیف
```
POST /discounts/apply-coupon/
{
    "coupon_code": "WELCOME20",
    "amount": 100000
}
```

### بررسی تخفیفات خودکار
```
POST /discounts/check-automatic/
{
    "user_id": 1,
    "doctor_id": 2,
    "amount": 100000
}
```

### تخفیفات موجود
```
GET /discounts/available/
```

## استفاده در کد

### محاسبه تخفیف
```python
from discounts.models import Discount

discount = Discount.objects.get(id=1)
amount = Decimal('100000')
discount_amount = discount.calculate_discount(amount)
```

### بررسی امکان استفاده
```python
can_use = discount.can_be_used_by_user(user)
```

### اعمال تخفیف به رزرو
```python
success, message = discount.apply_to_reservation(reservation, user)
```

## تست‌ها

سیستم شامل تست‌های جامع برای تمام عملکردها است:

```bash
python manage.py test discounts
```

### تست‌های موجود:
- ✅ ایجاد تخفیف
- ✅ ایجاد کد تخفیف
- ✅ محاسبه تخفیف درصدی
- ✅ محاسبه تخفیف مبلغ ثابت
- ✅ حداکثر مبلغ تخفیف
- ✅ اعتبار تخفیف
- ✅ تخفیفات خودکار
- ✅ گزارش‌گیری
- ✅ محدودیت استفاده

## کدهای تخفیف نمونه

پس از اجرای `create_sample_discounts`، کدهای زیر در دسترس خواهند بود:

- `WELCOME20`: تخفیف ۲۰ درصدی ویژه
- `SAVE50K`: تخفیف ۵۰ هزار تومانی
- `NEWPATIENT`: تخفیف ویژه بیماران جدید
- `LOYALTY10`: تخفیف وفاداری

## امنیت

- ✅ اعتبارسنجی کدهای تخفیف
- ✅ بررسی محدودیت‌های استفاده
- ✅ جلوگیری از استفاده مکرر
- ✅ ردیابی تمام استفاده‌ها

## عملکرد

- ✅ کش کردن تخفیفات فعال
- ✅ ایندکس‌گذاری مناسب دیتابیس
- ✅ کوئری‌های بهینه شده

## پشتیبانی

برای مشکلات و سوالات:
1. بررسی لاگ‌های Django
2. بررسی وضعیت تخفیفات در پنل ادمین
3. اجرای تست‌ها برای تشخیص مشکل

## توسعه آینده

- [ ] تخفیفات گروهی
- [ ] تخفیفات بر اساس موقعیت جغرافیایی
- [ ] یکپارچگی با سیستم‌های پرداخت
- [ ] تخفیفات شخصی‌سازی شده
- [ ] API GraphQL

---

**نسخه**: 1.0.0  
**تاریخ**: ۱۴۰۳/۱۰/۱۵  
**توسعه‌دهنده**: تیم Dr. Turn 