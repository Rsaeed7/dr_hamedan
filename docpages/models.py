from django.db import models
from django.utils import timezone
from doctors.models import Doctor

class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='published')
    
    def __str__(self):
        return f"{self.doctor} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']
        
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Comment by {self.name} on {self.post.title}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Comments'
