# راهنمای پشتیبانی از ویدیو در سیستم دکتر همدان

## نمای کلی

سیستم دکتر همدان از آپلود و نمایش ویدیو در پست‌های پزشکان پشتیبانی کامل می‌کند. این قابلیت به پزشکان اجازه می‌دهد تا ویدیوهای آموزشی، توضیحات درمانی، و محتوای تخصصی خود را با بیماران به اشتراک بگذارند.

## ویژگی‌های اصلی

### 🎥 انواع رسانه پشتیبانی شده
- **تصاویر**: JPG, JPEG, PNG, GIF, WebP
- **ویدیوها**: MP4, AVI, MOV, WMV, FLV, WebM

### 📏 محدودیت‌های حجم فایل
- **تصاویر**: حداکثر 10 مگابایت
- **ویدیوها**: حداکثر 50 مگابایت

### 🔒 قوانین آپلود
- در هر پست فقط یک نوع رسانه مجاز است (تصویر یا ویدیو، نه هر دو)
- سیستم به طور خودکار نوع رسانه را تشخیص می‌دهد
- اعتبارسنجی فایل در سمت سرور و کلاینت انجام می‌شود

## راهنمای استفاده برای پزشکان

### 1. ایجاد پست جدید با ویدیو

1. وارد داشبورد خود شوید
2. روی "پست‌های من" کلیک کنید
3. دکمه "ایجاد پست جدید" را انتخاب کنید
4. عنوان و محتوای پست را وارد کنید
5. در بخش "رسانه":
   - روی "انتخاب ویدیو" کلیک کنید
   - ویدیوی مورد نظر را از کامپیوتر خود انتخاب کنید
   - پیش‌نمایش ویدیو نمایش داده خواهد شد
6. برچسب‌های پزشکی مناسب را اضافه کنید
7. پست را منتشر کنید یا به عنوان پیش‌نویس ذخیره کنید

### 2. ویرایش پست موجود

1. در صفحه "پست‌های من" روی "ویرایش" پست مورد نظر کلیک کنید
2. برای تغییر ویدیو:
   - ویدیو جدید را انتخاب کنید (ویدیو قبلی جایگزین می‌شود)
   - یا "حذف ویدیو" را برای حذف کامل انتخاب کنید
3. تغییرات را ذخیره کنید

### 3. مشاهده پست‌ها

- در لیست پست‌ها، ویدیوها با کنترل‌های پخش نمایش داده می‌شوند
- بیماران می‌توانند مستقیماً از صفحه پست ویدیو را پخش کنند
- ویدیوها در صفحه جزئیات پست با کنترل‌های کامل نمایش داده می‌شوند

## راهنمای فنی برای توسعه‌دهندگان

### ساختار مدل

```python
class Post(models.Model):
    MEDIA_TYPE_CHOICES = (
        ('none', 'بدون رسانه'),
        ('image', 'تصویر'),
        ('video', 'ویدیو'),
    )
    
    # فیلدهای رسانه
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='none')
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    video = models.FileField(upload_to='post_videos/', blank=True, null=True)
```

### اعتبارسنجی فایل

```python
def validate_file_size(value):
    """اعتبارسنجی حجم فایل - حداکثر 50MB برای ویدیو، 10MB برای تصویر"""
    filesize = value.size
    if value.name.lower().endswith(('.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm')):
        if filesize > 50 * 1024 * 1024:  # 50MB
            raise ValidationError("حداکثر حجم ویدیو 50 مگابایت است.")
```

### نمایش در قالب

#### 1. لیست پست‌ها
```html
{% if post.media_type == 'video' and post.video %}
    <div class="w-full h-48 bg-black rounded-t-lg overflow-hidden">
        <video 
            src="{{ post.video.url }}" 
            class="w-full h-full object-cover"
            controls
            preload="metadata"
        >
            مرورگر شما از پخش ویدیو پشتیبانی نمی‌کند.
        </video>
    </div>
{% endif %}
```

#### 2. جزئیات پست
```html
{% if post.media_type == 'video' and post.video %}
    <div class="video-container">
        <video controls preload="metadata" class="w-full">
            <source src="{{ post.video.url }}" type="video/mp4">
            مرورگر شما از پخش ویدیو پشتیبانی نمی‌کند.
        </video>
    </div>
{% endif %}
```

### JavaScript برای آپلود

```javascript
// مدیریت آپلود ویدیو
videoInput.addEventListener('change', function(e) {
    if (e.target.files && e.target.files[0]) {
        // پاک کردن تصویر در صورت انتخاب ویدیو
        imageInput.value = '';
        imagePreview.classList.add('hidden');
        
        const file = e.target.files[0];
        const url = URL.createObjectURL(file);
        
        // نمایش پیش‌نمایش ویدیو
        document.getElementById('video-source').src = url;
        document.getElementById('video-preview-video').load();
        videoPreview.classList.remove('hidden');
    }
});
```

## بهینه‌سازی عملکرد

### 1. تنظیمات ویدیو
- **preload="metadata"**: بارگیری سریع‌تر صفحه با پیش‌بارگیری metadata
- **object-fit: cover**: نمایش بهتر ویدیو در ابعاد مختلف

### 2. تنظیمات سرور
```python
# در settings.py
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# محدودیت حجم آپلود
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
```

### 3. تنظیمات Nginx (برای production)
```nginx
# افزایش حد آپلود فایل
client_max_body_size 50M;

# بهینه‌سازی سرو فایل‌های رسانه
location /media/ {
    alias /path/to/media/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## امکانات پیشرفته

### 1. فیلتر براساس نوع رسانه
```python
# فیلتر پست‌های دارای ویدیو
video_posts = Post.objects.filter(media_type='video')

# فیلتر پست‌های دارای تصویر
image_posts = Post.objects.filter(media_type='image')
```

### 2. آمار رسانه
```python
def get_media_stats(self):
    """آمار نوع رسانه پست‌های پزشک"""
    posts = self.posts.all()
    return {
        'total': posts.count(),
        'with_video': posts.filter(media_type='video').count(),
        'with_image': posts.filter(media_type='image').count(),
        'no_media': posts.filter(media_type='none').count(),
    }
```

## نکات امنیتی

### 1. اعتبارسنجی نوع فایل
- بررسی پسوند فایل
- بررسی mime type
- اسکن ویروس (برای production)

### 2. مدیریت فضای ذخیره‌سازی
- پاک‌سازی فایل‌های حذف شده
- فشرده‌سازی ویدیوها (اختیاری)
- پشتیبان‌گیری منظم

## عیب‌یابی

### مشکلات رایج:

1. **ویدیو پخش نمی‌شود**
   - بررسی فرمت فایل
   - بررسی حجم فایل
   - بررسی تنظیمات مرورگر

2. **خطای آپلود**
   - بررسی محدودیت حجم سرور
   - بررسی مجوزهای پوشه media
   - بررسی فضای دیسک

3. **کیفیت پایین ویدیو**
   - استفاده از فرمت بهینه (MP4)
   - تنظیم کیفیت مناسب قبل از آپلود

## راهنمای بهترین عملکردها

### برای پزشکان:
1. از ویدیوهای کوتاه و مفید استفاده کنید (زیر 5 دقیقه)
2. کیفیت ویدیو را متناسب با محتوا انتخاب کنید
3. عنوان و توضیحات مناسب برای ویدیو بنویسید
4. از برچسب‌های پزشکی مرتبط استفاده کنید

### برای توسعه‌دهندگان:
1. همیشه فایل‌های قدیمی را هنگام تغییر پاک کنید
2. از CDN برای سرو فایل‌های رسانه استفاده کنید
3. سیستم فشرده‌سازی خودکار پیاده‌سازی کنید
4. مانیتورینگ فضای ذخیره‌سازی داشته باشید

این سیستم ویدیو کاملاً تست شده و آماده استفاده در محیط تولید است. 