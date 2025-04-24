from django.db import models
from django.utils import timezone
from doctors.models import Doctor

class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='posts', verbose_name='پزشک')
    title = models.CharField(max_length=200, verbose_name='عنوان')
    content = models.TextField(verbose_name='محتوا')
    image = models.ImageField(upload_to='post_images/', blank=True, null=True, verbose_name='تصویر')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    likes = models.PositiveIntegerField(default=0, verbose_name='لایک‌ها')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='published', verbose_name='وضعیت')
    
    def __str__(self):
        return f"{self.doctor} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'پست'
        verbose_name_plural = 'پست‌ها'
        
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='پست')
    name = models.CharField(max_length=100, verbose_name='نام')
    email = models.EmailField(verbose_name='ایمیل')
    body = models.TextField(verbose_name='متن')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    approved = models.BooleanField(default=False, verbose_name='تایید شده')
    
    def __str__(self):
        return f"Comment by {self.name} on {self.post.title}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'نظر'
        verbose_name_plural = 'نظرات'
