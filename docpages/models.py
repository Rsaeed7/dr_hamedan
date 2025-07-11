# from django.contrib.auth.models import User
from django.db import models
from user.models import User
from django.utils import timezone
from doctors.models import Doctor
from django.urls import reverse
from django_jalali.db import models as jmodels
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator


def validate_file_size(value):
    """Validate file size - max 50MB for videos, 10MB for images"""
    filesize = value.size
    if value.name.lower().endswith(('.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm')):
        # Video files - max 50MB
        if filesize > 50 * 1024 * 1024:
            raise ValidationError("حداکثر حجم ویدیو 50 مگابایت است.")
    else:
        # Image files - max 10MB
        if filesize > 10 * 1024 * 1024:
            raise ValidationError("حداکثر حجم تصویر 10 مگابایت است.")


class MedicalLens(models.Model):
    """Medical specialties and topics for tagging posts"""
    name = models.CharField(max_length=100, unique=True, verbose_name='نام')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    color = models.CharField(max_length=7, default='#3b82f6', verbose_name='رنگ تگ')  # Hex color
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name = 'لنز پزشکی'
        verbose_name_plural = 'لنزهای پزشکی'


class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )
    
    MEDIA_TYPE_CHOICES = (
        ('none', 'بدون رسانه'),
        ('image', 'تصویر'),
        ('video', 'ویدیو'),
    )
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='posts', verbose_name='پزشک')
    title = models.CharField(max_length=200, verbose_name='عنوان')
    content = models.TextField(verbose_name='محتوا')
    
    # Media fields - only one can be used
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='none', verbose_name='نوع رسانه')
    image = models.ImageField(
        upload_to='post_images/', 
        blank=True, 
        null=True, 
        verbose_name='تصویر',
        validators=[
            validate_file_size,
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])
        ]
    )
    video = models.FileField(
        upload_to='post_videos/', 
        blank=True, 
        null=True, 
        verbose_name='ویدیو',
        validators=[
            validate_file_size,
            FileExtensionValidator(allowed_extensions=['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'])
        ]
    )
    
    # Medical tagging
    medical_lenses = models.ManyToManyField(MedicalLens, blank=True, verbose_name='لنزهای پزشکی')
    
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    likes_count = models.PositiveIntegerField(default=0, verbose_name='تعداد لایک‌ها')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='published', verbose_name='وضعیت')
    
    def clean(self):
        """Ensure only one media type is selected"""
        super().clean()
        media_count = sum([bool(self.image), bool(self.video)])
        
        if media_count > 1:
            raise ValidationError('فقط می‌توانید یک نوع رسانه (تصویر یا ویدیو) انتخاب کنید.')
        
        # Set media_type based on uploaded media
        if self.image:
            self.media_type = 'image'
        elif self.video:
            self.media_type = 'video'
        else:
            self.media_type = 'none'
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_media_url(self):
        """Get the URL of the associated media"""
        if self.media_type == 'image' and self.image:
            return self.image.url
        elif self.media_type == 'video' and self.video:
            return self.video.url
        return None
    
    def get_like_count(self):
        """Get actual like count from PostLike model"""
        return self.post_likes.count()
    
    def is_liked_by_user(self, user):
        """Check if post is liked by specific user"""
        if not user.is_authenticated:
            return False
        return self.post_likes.filter(user=user).exists()
    
    def __str__(self):
        return f"{self.doctor} - {self.title}"

    def get_absolute_url(self):
        return reverse('docpages:post_detail', args=[str(self.id)])

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'پست'
        verbose_name_plural = 'پست‌ها'


class PostLike(models.Model):
    """Track individual user likes for posts"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes', verbose_name='پست')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_posts', verbose_name='کاربر')
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ لایک')
    
    class Meta:
        unique_together = ('post', 'user')
        verbose_name = 'لایک پست'
        verbose_name_plural = 'لایک‌های پست'
    
    def __str__(self):
        return f"{self.user} - {self.post.title}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='پست')
    name = models.CharField(max_length=100, verbose_name='نام')
    body = models.TextField(verbose_name='متن')
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    approved = models.BooleanField(default=False, verbose_name='تایید شده')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر', related_name='post_comments',
                             null=True, blank=True)
    
    def __str__(self):
        return f"Comment by {self.name} on {self.post.title}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'نظر'
        verbose_name_plural = 'نظرات'
