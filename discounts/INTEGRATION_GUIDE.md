# سیستم تخفیف دکتر ترن - راهنمای یکپارچه‌سازی

## نصب و راه‌اندازی

### 1. اضافه کردن اپ به تنظیمات
```python
# در فایل settings.py
INSTALLED_APPS = [
    # ...
    'discounts.apps.DiscountsConfig',
    # ...
]
```

### 2. اضافه کردن URLها
```python
# در فایل urls.py اصلی
urlpatterns = [
    # ...
    path('discounts/', include('discounts.urls')),
    # ...
]
```

### 3. اجرای مایگریشن‌ها
```bash
python manage.py makemigrations discounts
python manage.py migrate discounts
```

### 4. ایجاد داده‌های نمونه
```bash
python manage.py create_sample_discounts
```

## یکپارچه‌سازی با فرم رزرو

### 1. اضافه کردن ویجت تخفیف به تمپلیت رزرو

```html
<!-- در فایل تمپلیت رزرو -->
{% load static %}

<!-- اضافه کردن شناسه رزرو -->
<div data-reservation-id="{{ reservation.id }}" style="display: none;"></div>

<!-- اضافه کردن ویجت تخفیف -->
{% include 'discounts/discount_widget.html' %}

<!-- نمایش مبلغ با قابلیت بروزرسانی -->
<div class="amount-display">
    <span>مبلغ قابل پرداخت: </span>
    <span data-amount-display>{{ reservation.amount|floatformat:0 }} تومان</span>
</div>
```

### 2. بروزرسانی مدل Reservation

```python
# در فایل reservations/models.py
from discounts.models import DiscountUsage

class Reservation(models.Model):
    # فیلدهای موجود...
    
    def get_final_amount(self):
        """محاسبه مبلغ نهایی با در نظر گیری تخفیف"""
        if hasattr(self, 'discount_usage'):
            return self.discount_usage.final_amount
        return self.amount
    
    def has_discount(self):
        """بررسی اعمال تخفیف"""
        return hasattr(self, 'discount_usage')
```

### 3. بروزرسانی ویوهای پرداخت

```python
# در فایل wallet/views.py
def process_payment(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    # استفاده از مبلغ نهایی (با تخفیف)
    final_amount = reservation.get_final_amount()
    
    # ادامه پردازش پرداخت...
```

## استفاده از APIهای تخفیف

### 1. اعمال کد تخفیف
```javascript
fetch('/discounts/api/apply-coupon/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
        coupon_code: 'WELCOME20',
        reservation_id: reservationId
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        // بروزرسانی UI
        updateAmountDisplay(data.final_amount);
    }
});
```

### 2. بررسی تخفیفات خودکار
```javascript
fetch('/discounts/api/check-automatic/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
        reservation_id: reservationId
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        // نمایش تخفیف اعمال شده
        showDiscountApplied(data);
    }
});
```

### 3. دریافت تخفیفات قابل اعمال
```javascript
fetch(`/discounts/api/available/?reservation_id=${reservationId}`)
.then(response => response.json())
.then(data => {
    if (data.success) {
        displayAvailableDiscounts(data.discounts);
    }
});
```

## مدیریت تخفیفات در پنل ادمین

### 1. ایجاد تخفیف جدید
- وارد پنل ادمین شوید
- به بخش "سیستم تخفیف" بروید
- روی "تخفیفات" کلیک کنید
- "افزودن تخفیف" را انتخاب کنید

### 2. تنظیم شرایط تخفیف
- **نوع تخفیف**: درصدی یا مبلغ ثابت
- **قابل اعمال برای**: همه، پزشک خاص، تخصص خاص، کلینیک خاص، بیماران جدید، بیماران قدیمی
- **محدودیت‌ها**: حداقل مبلغ، حداکثر تخفیف، تعداد استفاده
- **تاریخ اعتبار**: تاریخ شروع و پایان

### 3. ایجاد کد تخفیف
- در صفحه ویرایش تخفیف
- به بخش "کدهای تخفیف" بروید
- کد دلخواه را وارد کنید

### 4. تنظیم تخفیف خودکار
- به بخش "تخفیفات خودکار" بروید
- شرایط خودکار را تعریف کنید:
  - اولین نوبت
  - حداقل تعداد نوبت قبلی
  - آخر هفته
  - روزهای خاص

## نکات مهم

### 1. امنیت
- همیشه از CSRF token استفاده کنید
- ورودی‌های کاربر را اعتبارسنجی کنید
- دسترسی‌ها را بررسی کنید

### 2. عملکرد
- از select_related و prefetch_related استفاده کنید
- کوئری‌های پایگاه داده را بهینه کنید
- کش مناسب پیاده‌سازی کنید

### 3. تجربه کاربری
- پیام‌های واضح و مفید نمایش دهید
- وضعیت loading را نشان دهید
- خطاها را به درستی مدیریت کنید

## مثال کامل یکپارچه‌سازی

```html
<!-- reservation_form.html -->
{% extends 'base.html' %}
{% load jformat %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <form id="reservation-form" method="post">
        {% csrf_token %}
        
        <!-- اطلاعات رزرو -->
        <div class="reservation-details">
            <!-- فیلدهای رزرو... -->
        </div>
        
        <!-- ویجت تخفیف -->
        <div data-reservation-id="{{ reservation.id }}"></div>
        {% include 'discounts/discount_widget.html' %}
        
        <!-- خلاصه پرداخت -->
        <div class="payment-summary">
            <div class="amount-row">
                <span>مبلغ نهایی:</span>
                <span data-amount-display class="font-bold">
                    {{ reservation.get_final_amount|floatformat:0 }} تومان
                </span>
            </div>
        </div>
        
        <!-- دکمه پرداخت -->
        <button type="submit" class="btn btn-primary">
            پرداخت و تکمیل رزرو
        </button>
    </form>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // بررسی خودکار تخفیفات هنگام بارگذاری صفحه
    if (window.discountWidget) {
        window.discountWidget.checkAutomaticDiscounts();
    }
});
</script>
{% endblock %}
```

## کدهای تست

برای تست سیستم از کدهای تخفیف زیر استفاده کنید:

- `WELCOME20`: تخفیف ۲۰ درصدی ویژه
- `SAVE50K`: تخفیف ۵۰ هزار تومانی
- `NEWPATIENT`: تخفیف ویژه بیماران جدید
- `LOYALTY10`: تخفیف وفاداری

## پشتیبانی و توسعه

برای سوالات و مشکلات:
1. لاگ‌های Django را بررسی کنید
2. از ابزارهای توسعه‌دهنده مرورگر استفاده کنید
3. تست‌های واحد بنویسید
4. مستندات API را مطالعه کنید 