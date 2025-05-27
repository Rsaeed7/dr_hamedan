import os
import sys
import django

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dr_turn.settings")
django.setup()

# Now we can import Django models
from reservations.models import ReservationDay
from datetime import datetime, timedelta
import jdatetime

# Function to print date details
def print_date_details(date):
    # Python's weekday: 0=Monday, 6=Sunday
    python_weekday = date.weekday()
    
    # Convert to Persian calendar
    jalali_date = jdatetime.date.fromgregorian(date=date)
    
    # Map weekdays
    python_weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    persian_weekday_names = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
    
    # Calculate Persian weekday (0=Saturday)
    # Method 1: using formula
    persian_weekday_formula = (python_weekday + 2) % 7
    
    # Method 2: using logic
    if python_weekday == 5:  # Saturday in Python
        persian_weekday_logic = 0  # Saturday in Persian
    elif python_weekday == 6:  # Sunday in Python
        persian_weekday_logic = 1  # Sunday in Persian
    else:
        persian_weekday_logic = python_weekday + 2
    
    # Print info
    print(f"Date: {date}")
    print(f"  Jalali: {jalali_date}")
    print(f"  Python weekday: {python_weekday} ({python_weekday_names[python_weekday]})")
    print(f"  Persian weekday (formula): {persian_weekday_formula} ({persian_weekday_names[persian_weekday_formula]})")
    print(f"  Persian weekday (logic): {persian_weekday_logic} ({persian_weekday_names[persian_weekday_logic]})")
    print()

# Get today and next 7 days
today = datetime.now().date()
print("Today and next 7 days:")
for i in range(8):
    date = today + timedelta(days=i)
    print_date_details(date)

# Get ReservationDay objects for this period
days = ReservationDay.objects.filter(
    date__gte=today,
    date__lte=today + timedelta(days=7),
    published=True
)

print("\nReservation days in database:")
for day in days:
    print(f"ReservationDay: {day.date} (Published: {day.published})")
    print_date_details(day.date) 