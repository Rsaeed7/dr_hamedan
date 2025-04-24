from django.db import models
from django.contrib.auth.models import User

class PatientsFile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    national_id = models.CharField(max_length=20, blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def get_reservations(self):
        """Get all reservations for this patient"""
        from reservations.models import Reservation
        return Reservation.objects.filter(patient=self)
    
    def get_upcoming_appointments(self):
        """Get upcoming appointments for this patient"""
        from reservations.models import Reservation
        from django.utils import timezone
        
        return Reservation.objects.filter(
            patient=self,
            status__in=['pending', 'confirmed'],
            day__date__gte=timezone.now().date()
        ).order_by('day__date', 'time')
    
    def get_past_appointments(self):
        """Get past appointments for this patient"""
        from reservations.models import Reservation
        from django.utils import timezone
        
        return Reservation.objects.filter(
            patient=self,
            day__date__lt=timezone.now().date()
        ).order_by('-day__date', '-time')
