from django.db import models
from django_jalali.db import models as jmodels
from patients.models import PatientsFile
from doctors.models import Doctor

class ReservationDay(models.Model):
    date = jmodels.jDateField()
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.date} - {'Published' if self.published else 'Unpublished'}"
    
    class Meta:
        verbose_name_plural = "Reservation Days"

class Reservation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    day = models.ForeignKey(ReservationDay, on_delete=models.CASCADE, related_name='reservations')
    patient = models.ForeignKey(PatientsFile, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='reservations')
    time = models.TimeField()
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    transaction = models.ForeignKey('wallet.Transaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        patient_name = self.patient.name if self.patient else "Guest"
        return f"{patient_name} - {self.doctor} - {self.day.date} {self.time}"
    
    def confirm_appointment(self):
        """Confirm this appointment"""
        if self.status == 'pending' and self.payment_status == 'paid':
            self.status = 'confirmed'
            self.save()
            # TODO: Send confirmation email/notification
            return True
        return False
    
    def cancel_appointment(self, refund=True):
        """Cancel this appointment with optional refund"""
        if self.status in ['pending', 'confirmed']:
            self.status = 'cancelled'
            
            # Handle refund if requested and payment was made
            if refund and self.payment_status == 'paid':
                self.payment_status = 'refunded'
                
                # Process refund in wallet app
                if self.transaction:
                    from wallet.models import Transaction
                    Transaction.objects.create(
                        user=self.transaction.user,
                        amount=self.amount,
                        transaction_type='refund',
                        related_transaction=self.transaction,
                        status='completed',
                        description=f"Refund for cancelled appointment - {self}"
                    )
            
            self.save()
            # TODO: Send cancellation email/notification
            return True
        return False
    
    def complete_appointment(self):
        """Mark appointment as completed"""
        if self.status == 'confirmed' and self.payment_status == 'paid':
            self.status = 'completed'
            self.save()
            # TODO: Send completion email/notification
            return True
        return False

    class Meta:
        unique_together = ('day', 'doctor', 'time')
