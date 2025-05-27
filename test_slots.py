import os
import sys
import django

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dr_turn.settings")
django.setup()

# Import Django models
from doctors.models import Doctor, DoctorAvailability
from datetime import datetime, timedelta

# Get doctor with ID 4
doctor = Doctor.objects.get(id=4)
print(f"Doctor: {doctor}")

# Print doctor availabilities
availabilities = DoctorAvailability.objects.filter(doctor=doctor)
print("\nDoctor availabilities:")
for avail in availabilities:
    print(f"  Day {avail.day_of_week} ({avail.get_day_of_week_display()}): {avail.start_time} - {avail.end_time}")

# Check next 7 days
today = datetime.now().date()
print("\nChecking next 7 days for available slots:")
for i in range(7):
    date = today + timedelta(days=i)
    python_weekday = date.weekday()
    persian_weekday = (python_weekday + 2) % 7
    
    # Get Persian weekday name
    persian_weekday_names = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
    
    # Get available slots
    slots = doctor.get_available_slots(date)
    
    print(f"Date: {date} ({persian_weekday_names[persian_weekday]})")
    print(f"  Persian weekday: {persian_weekday}")
    print(f"  Available slots: {len(slots)}")
    if slots:
        print(f"    First 3 slots: {slots[:3]}")
    print() 