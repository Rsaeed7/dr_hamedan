import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dr_turn.settings')
django.setup()

from doctors.models import Doctor, DoctorAvailability
from reservations.models import ReservationDay, Reservation
from datetime import datetime, time, timedelta
import jdatetime

def test_complete_workflow():
    # 1. Get the doctor and create a weekday availability
    doctor = Doctor.objects.first()
    print(f"Testing with doctor: {doctor}")
    
    # 2. Set consultation duration to make sure it's reasonable
    doctor.consultation_duration = 30
    doctor.save()
    print(f"Set consultation duration to {doctor.consultation_duration} minutes")
    
    # 3. Create a Saturday availability (day 0)
    saturday_avail, created = DoctorAvailability.objects.update_or_create(
        doctor=doctor,
        day_of_week=0,  # Saturday
        defaults={
            'start_time': time(10, 12),
            'end_time': time(13, 13)
        }
    )
    print(f"Saturday availability {'created' if created else 'updated'}: {saturday_avail}")
    
    # 4. Create a Monday availability (day 2)
    monday_avail, created = DoctorAvailability.objects.update_or_create(
        doctor=doctor,
        day_of_week=2,  # Monday
        defaults={
            'start_time': time(21, 47),
            'end_time': time(22, 47)
        }
    )
    print(f"Monday availability {'created' if created else 'updated'}: {monday_avail}")
    
    # 5. Use the BookingService to find available days
    from reservations.services import BookingService
    
    available_days = BookingService.get_available_days_for_doctor(doctor, days_ahead=30)
    print(f"\nFound {len(available_days)} available days in the next 30 days:")
    
    for day_info in available_days:
        date = day_info['date']
        jalali_date = day_info['jalali_date']
        slots = day_info['slots']
        
        # Persian day name
        persian_weekday = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"][date.weekday()]
        
        print(f"- {date} ({persian_weekday}) - {jalali_date}: {len(slots)} time slots available")
        if slots:
            print(f"  First slot: {slots[0]}, Last slot: {slots[-1]}")
    
    print("\nTest completed successfully")

if __name__ == "__main__":
    test_complete_workflow() 