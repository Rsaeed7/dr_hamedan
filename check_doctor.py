import os
import sys
import django

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dr_turn.settings")
django.setup()

# Now we can import Django models
from doctors.models import Doctor, DoctorAvailability
from reservations.models import ReservationDay, Reservation
from datetime import datetime, timedelta

# Get doctor with ID 4
doctor = Doctor.objects.get(id=4)
print(f"Doctor: {doctor}")
print(f"Is available: {doctor.is_available}")
print(f"Consultation duration: {doctor.consultation_duration} minutes")

# Check availabilities
print("\nAvailabilities:")
availabilities = DoctorAvailability.objects.filter(doctor=doctor)
for avail in availabilities:
    print(f"  Day {avail.day_of_week} ({avail.get_day_of_week_display()}): {avail.start_time} - {avail.end_time}")

# Check reservation days
today = datetime.now().date()
print("\nReservation days for next 7 days:")
days = ReservationDay.objects.filter(
    date__gte=today,
    date__lte=today + timedelta(days=7),
    published=True
)
for day in days:
    print(f"  {day.date} (Published: {day.published})")

# Test the get_available_slots method
print("\nTesting get_available_slots for each day:")
for day in days:
    slots = doctor.get_available_slots(day.date)
    weekday = day.date.weekday()
    persian_day_of_week = (weekday + 2) % 7
    print(f"  {day.date} - Persian weekday: {persian_day_of_week} - Slots: {len(slots)}")
    if slots:
        print(f"    First 3 slots: {slots[:3]}")
    else:
        print("    No slots available")
        # Check if doctor has availability for this day
        avail = availabilities.filter(day_of_week=persian_day_of_week).first()
        if avail:
            print(f"    Doctor has availability for this day: {avail}")
            # Check if there are conflicting reservations
            reservations = Reservation.objects.filter(
                day=day,
                doctor=doctor,
                status__in=['pending', 'confirmed']
            )
            print(f"    Existing reservations: {reservations.count()}")
        else:
            print("    Doctor has no availability for this day") 