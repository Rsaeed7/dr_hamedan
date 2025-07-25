#!/usr/bin/env python
"""
Test SMS Fix with Mock Data
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dr_turn.settings')
django.setup()

from django.utils import timezone
from user.models import User
from patients.models import PatientsFile
from doctors.models import Doctor
from reservations.models import Reservation, ReservationDay
from utils.sms_service import sms_service


def create_test_data():
    """Create test data for SMS testing"""
    print("=== Creating Test Data ===")
    
    # Create test user
    user, created = User.objects.get_or_create(
        phone='09384104825',
        defaults={
            'first_name': 'علی',
            'last_name': 'احمدی',
            'email': 'test@example.com'
        }
    )
    
    if created:
        print(f"✅ Created test user: {user.phone}")
    else:
        print(f"📝 Using existing user: {user.phone}")
    
    # Create test patient
    patient, created = PatientsFile.objects.get_or_create(
        user=user,
        defaults={
            'phone': '09384104825',
            'national_id': '1234567890',
            'gender': 'male'
        }
    )
    
    if created:
        print(f"✅ Created test patient: {patient.name}")
    else:
        print(f"📝 Using existing patient: {patient.name}")
    
    # Create test doctor
    doctor_user, created = User.objects.get_or_create(
        phone='09184058726',
        defaults={
            'first_name': 'دکتر',
            'last_name': 'محمدی',
            'email': 'doctor@example.com'
        }
    )
    
    if created:
        print(f"✅ Created test doctor user: {doctor_user.phone}")
    else:
        print(f"📝 Using existing doctor user: {doctor_user.phone}")
    
    # Create test doctor
    doctor, created = Doctor.objects.get_or_create(
        user=doctor_user,
        defaults={
            'specialization': 'داخلی',
            'license_number': '12345'
        }
    )
    
    if created:
        print(f"✅ Created test doctor: {doctor}")
    else:
        print(f"📝 Using existing doctor: {doctor}")
    
    # Create test reservation day
    tomorrow = timezone.now().date() + timezone.timedelta(days=1)
    day, created = ReservationDay.objects.get_or_create(
        doctor=doctor,
        date=tomorrow,
        defaults={'is_active': True}
    )
    
    if created:
        print(f"✅ Created test reservation day: {day.date}")
    else:
        print(f"📝 Using existing reservation day: {day.date}")
    
    # Use a specific time for the reservation
    reservation_time = timezone.time(10, 0)  # 10:00 AM
    print(f"✅ Using reservation time: {reservation_time}")
    
    # Create test reservation
    reservation, created = Reservation.objects.get_or_create(
        patient=patient,
        doctor=doctor,
        day=day,
        time=reservation_time,
        defaults={
            'status': 'confirmed',
            'phone': patient.phone,  # This will be ignored by our fix
            'amount': 50000  # 50,000 tomans
        }
    )
    
    if created:
        print(f"✅ Created test reservation: {reservation.id}")
    else:
        print(f"📝 Using existing reservation: {reservation.id}")
    
    return reservation


def test_sms_functionality(reservation):
    """Test SMS functionality with the test reservation"""
    print("\n=== Testing SMS Functionality ===")
    
    print(f"Reservation ID: {reservation.id}")
    print(f"Patient: {reservation.patient.name}")
    print(f"Patient Phone: {reservation.patient.phone}")
    print(f"Doctor: {reservation.doctor.user.get_full_name()}")
    print(f"Date: {reservation.day.date}")
    print(f"Time: {reservation.time}")
    
    # Test 1: Direct SMS service
    print("\n--- Testing Direct SMS Service ---")
    try:
        result = sms_service.send_appointment_confirmation(reservation)
        print(f"Confirmation SMS result: {result}")
        
        if result.get('success'):
            print("✅ Direct SMS service works!")
        else:
            print(f"❌ Direct SMS failed: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Exception in direct SMS: {str(e)}")
    
    # Test 2: 24-hour reminder
    print("\n--- Testing 24-hour Reminder ---")
    try:
        result = sms_service.send_appointment_reminder(reservation, 24)
        print(f"24h reminder result: {result}")
        
        if result.get('success'):
            print("✅ 24-hour reminder works!")
        else:
            print(f"❌ 24-hour reminder failed: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Exception in 24h reminder: {str(e)}")
    
    # Test 3: 2-hour reminder
    print("\n--- Testing 2-hour Reminder ---")
    try:
        result = sms_service.send_appointment_reminder(reservation, 2)
        print(f"2h reminder result: {result}")
        
        if result.get('success'):
            print("✅ 2-hour reminder works!")
        else:
            print(f"❌ 2-hour reminder failed: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Exception in 2h reminder: {str(e)}")
    
    # Test 4: Cancellation SMS
    print("\n--- Testing Cancellation SMS ---")
    try:
        result = sms_service.send_appointment_cancellation(reservation)
        print(f"Cancellation SMS result: {result}")
        
        if result.get('success'):
            print("✅ Cancellation SMS works!")
        else:
            print(f"❌ Cancellation SMS failed: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Exception in cancellation SMS: {str(e)}")


def main():
    """Main test function"""
    print("🚀 Testing SMS Fix with Mock Data")
    print("=" * 50)
    
    # Create test data
    reservation = create_test_data()
    
    # Test SMS functionality
    test_sms_functionality(reservation)
    
    print("\n" + "=" * 50)
    print("✅ SMS fix test completed!")
    print("💡 Check the results above to see if SMS reminders work correctly")


if __name__ == "__main__":
    main() 