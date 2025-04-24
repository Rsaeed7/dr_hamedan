# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(_('شماره تماس'), max_length=15, blank=True, null=True)
    national_id = models.CharField(_('کد ملی'), max_length=10, blank=True, null=True)
    birth_date = models.DateField(_('تاریخ تولد'), blank=True, null=True)
    address = models.TextField(_('آدرس'), blank=True, null=True)
    profile_image = models.ImageField(_('تصویر پروفایل'), upload_to='profile_images/', blank=True, null=True)
    
    class Meta:
        verbose_name = _('پروفایل کاربر')
        verbose_name_plural = _('پروفایل‌های کاربران')
    
    def __str__(self):
        return f"{self.user.username} - {_('پروفایل')}"

# Signal to create user profile when a new user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)