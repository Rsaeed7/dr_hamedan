from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class Clinic(models.Model):
    name = models.CharField(_('نام کلینیک'), max_length=100)
    address = models.TextField(_('آدرس'))
    phone = models.CharField(_('تلفن'), max_length=15)
    email = models.EmailField(_('ایمیل'), blank=True, null=True)
    logo = models.ImageField(_('لوگو'), upload_to='clinics/', blank=True, null=True)
    description = models.TextField(_('توضیحات'), blank=True, null=True)
    
    # Clinic owner/administrator
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='administered_clinics')
    
    # Operating hours could be added here or in a separate model
    
    class Meta:
        verbose_name = _('کلینیک')
        verbose_name_plural = _('کلینیک ها')
    
    def __str__(self):
        return self.name
    
    def get_doctors(self):
        """Returns all doctors associated with this clinic"""
        return self.doctors.all()
    
    def get_appointments(self):
        """Returns all appointments at this clinic"""
        # Implementation to be added
        pass


class ClinicSpecialty(models.Model):
    """Specialties offered at a clinic"""
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='specialties')
    name = models.CharField(_('نام تخصص'), max_length=100)
    description = models.TextField(_('توضیحات'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('تخصص کلینیک')
        verbose_name_plural = _('تخصص های کلینیک')
        
    def __str__(self):
        return f"{self.clinic.name} - {self.name}"


class ClinicGallery(models.Model):
    """Images of the clinic for display"""
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(_('تصویر'), upload_to='clinics/gallery/')
    title = models.CharField(_('عنوان'), max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name = _('تصویر کلینیک')
        verbose_name_plural = _('گالری تصاویر کلینیک')
        
    def __str__(self):
        return f"{self.clinic.name} - {self.title or 'Image'}"
