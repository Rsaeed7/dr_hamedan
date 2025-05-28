#!/usr/bin/env python
import os
import sys
import django

sys.path.append('/home/siavash-rahimi/Desktop/dr_hamedan')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dr_turn.settings')
django.setup()

from doctors.models import Doctor, DoctorAvailability
from reservations.models import ReservationDay
from datetime import datetime, time, timedelta
import jdatetime

# Get the first doctor
doctor = Doctor.objects.first()
print(f'Testing for doctor: {doctor}')

# Create/update a Sunday availability from 8:00 to 8:30
avail, created = DoctorAvailability.objects.update_or_create(
    doctor=doctor,
    day_of_week=1,  # Sunday
    defaults={
        'start_time': time(8, 0),
        'end_time': time(8, 30)
    }
)
print(f'Availability {"created" if created else "updated"}: {avail}')

# Find next Sunday
today = datetime.now().date()
days_ahead = (7 - today.weekday() + 1) % 7
if days_ahead == 0:
    days_ahead = 7
next_sunday = today + timedelta(days=days_ahead)
print(f'Next Sunday: {next_sunday} (Jalali: {jdatetime.date.fromgregorian(date=next_sunday)})')

# Make sure the ReservationDay exists and is published
res_day, created = ReservationDay.objects.get_or_create(
    date=next_sunday,
    defaults={'published': True}
)
if not res_day.published:
    res_day.published = True
    res_day.save()
print(f'ReservationDay: {"created" if created else "exists"}, Published: {res_day.published}')

# Test available slots
slots = doctor.get_available_slots(next_sunday)
print(f'Available slots for {next_sunday}:')
for slot in slots:
    print(f'  - {slot}') 