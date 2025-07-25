#!/usr/bin/env python
"""
Test SMS Fix - Verify that SMS reminders work with patient phone numbers
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dr_turn.settings')
django.setup()

from reservations.models import Reservation
from utils.sms_service import sms_service
from sms_reminders.services import send_confirmation_sms, schedule_appointment_reminders


def test_sms_with_patient_phone():
    """Test SMS functionality with patient phone numbers"""
    print("=== Testing SMS with Patient Phone Numbers ===")
    
    # Get a sample reservation
    reservation = Reservation.objects.first()
    
    if not reservation:
        print("❌ No reservations found in database")
        return False
    
    print(f"Testing with reservation ID: {reservation.id}")
    
    # Check if patient exists
    if not reservation.patient:
        print("❌ Reservation has no patient")
        return False
    
    # Check patient phone number
    patient_phone = reservation.patient.phone
    print(f"Patient: {reservation.patient.name}")
    print(f"Patient Phone: {patient_phone}")
    
    if not patient_phone:
        print("❌ Patient has no phone number")
        return False
    
    # Test 1: Direct SMS service
    print("\n--- Testing Direct SMS Service ---")
    try:
        result = sms_service.send_appointment_confirmation(reservation)
        print(f"Confirmation SMS result: {result}")
        
        if result.get('success'):
            print("✅ Direct SMS service works!")
        else:
            print(f"❌ Direct SMS failed: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception in direct SMS: {str(e)}")
        return False
    
    # Test 2: SMS Reminder Service
    print("\n--- Testing SMS Reminder Service ---")
    try:
        confirmation = send_confirmation_sms(reservation)
        if confirmation:
            print(f"✅ SMS reminder service works! Reminder ID: {confirmation.id}")
        else:
            print("❌ SMS reminder service failed")
            return False
            
    except Exception as e:
        print(f"❌ Exception in SMS reminder service: {str(e)}")
        return False
    
    # Test 3: Schedule Reminders
    print("\n--- Testing Schedule Reminders ---")
    try:
        reminders = schedule_appointment_reminders(reservation)
        print(f"✅ Scheduled {len(reminders)} reminders")
        
        for reminder in reminders:
            print(f"  - {reminder.reminder_type}: {reminder.scheduled_time}")
            
    except Exception as e:
        print(f"❌ Exception scheduling reminders: {str(e)}")
        return False
    
    print("\n✅ All SMS tests passed!")
    return True


def check_reservation_data():
    """Check reservation data structure"""
    print("\n=== Checking Reservation Data Structure ===")
    
    reservation = Reservation.objects.first()
    if not reservation:
        print("❌ No reservations found")
        return
    
    print(f"Reservation ID: {reservation.id}")
    print(f"Has patient: {reservation.patient is not None}")
    
    if reservation.patient:
        print(f"Patient name: {reservation.patient.name}")
        print(f"Patient phone: {reservation.patient.phone}")
        print(f"Patient user: {reservation.patient.user}")
        
        if reservation.patient.user:
            print(f"User first name: {reservation.patient.user.first_name}")
            print(f"User last name: {reservation.patient.user.last_name}")
    
    # Check if reservation has direct phone field (it shouldn't)
    if hasattr(reservation, 'phone'):
        print(f"Reservation has direct phone: {reservation.phone}")
    else:
        print("✅ Reservation has no direct phone field (correct)")


def main():
    """Main test function"""
    print("🚀 Testing SMS Fix for Patient Phone Numbers")
    print("=" * 50)
    
    # Check data structure
    check_reservation_data()
    
    # Test SMS functionality
    success = test_sms_with_patient_phone()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 SMS fix is working correctly!")
        print("✅ Patient phone numbers are now properly accessed")
        print("✅ All SMS reminder types should work")
    else:
        print("❌ SMS fix needs more work")
    
    print("\n💡 Next steps:")
    print("  - Test with real phone numbers")
    print("  - Run management commands: python manage.py process_sms_reminders")
    print("  - Check SMS logs for success/failure")


if __name__ == "__main__":
    main() 