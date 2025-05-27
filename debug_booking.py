import os
import sys
import django

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dr_turn.settings")
django.setup()

# Import Django models
from doctors.models import Doctor, DoctorAvailability
from reservations.models import ReservationDay, Reservation
from reservations.services import BookingService
from datetime import datetime, timedelta
import jdatetime

# Get doctor with ID 4
doctor = Doctor.objects.get(id=4)
print(f"Doctor: {doctor}")
print(f"Is available: {doctor.is_available}")

# Print doctor availabilities
availabilities = DoctorAvailability.objects.filter(doctor=doctor)
print("\nDoctor availabilities:")
for avail in availabilities:
    print(f"  Day {avail.day_of_week} ({avail.get_day_of_week_display()}): {avail.start_time} - {avail.end_time}")

# Test BookingService.get_available_days_for_doctor
available_days = BookingService.get_available_days_for_doctor(doctor.id, days_ahead=30)
print(f"\nFound {len(available_days)} available days for booking:")

for day in available_days:
    date = day['date']
    slots = day['slots']
    jalali_date = day['jalali_date']
    
    # Calculate weekday
    python_weekday = date.weekday()
    persian_weekday = (python_weekday + 2) % 7
    
    # Get Persian weekday name
    persian_weekday_names = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
    
    print(f"Date: {date} ({persian_weekday_names[persian_weekday]})")
    print(f"  Jalali date: {jalali_date}")
    print(f"  Persian weekday: {persian_weekday}")
    print(f"  Available slots: {len(slots)}")
    if slots:
        print(f"    First 3 slots: {slots[:3]}")
    print()

# Debug ReservationDay objects for this doctor
today = datetime.now().date()
for i in range(7):
    date = today + timedelta(days=i)
    python_weekday = date.weekday()
    persian_weekday = (python_weekday + 2) % 7
    
    # Get Persian weekday name
    persian_weekday_names = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
    
    # Check if we have a reservation day
    reservation_day = ReservationDay.objects.filter(date=date).first()
    
    print(f"Date: {date} ({persian_weekday_names[persian_weekday]})")
    print(f"  ReservationDay exists: {reservation_day is not None}")
    if reservation_day:
        print(f"  Published: {reservation_day.published}")
    print() 