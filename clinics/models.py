from django.db import models
from django.contrib.auth.models import User

class Clinic(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    logo = models.ImageField(upload_to='clinic_logos/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='administered_clinics')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def get_doctors(self):
        return self.doctors.all()
    
    def get_all_appointments(self):
        from reservations.models import Reservation
        doctors = self.get_doctors()
        return Reservation.objects.filter(doctor__in=doctors)

class ClinicSpecialty(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='specialties')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.clinic.name} - {self.name}"
    
    class Meta:
        verbose_name_plural = "Clinic Specialties"

class ClinicGallery(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='clinic_gallery/')
    title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.clinic.name} Gallery Image - {self.id}"
    
    class Meta:
        verbose_name_plural = "Clinic Galleries"
