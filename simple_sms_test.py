#!/usr/bin/env python
"""
Simple SMS Test - Test SMS service directly
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dr_turn.settings')
django.setup()

from utils.sms_service import sms_service


def test_sms_service():
    """Test SMS service directly"""
    print("=== Testing SMS Service Directly ===")
    
    # Test 1: Basic SMS sending
    print("\n--- Testing Basic SMS Sending ---")
    try:
        result = sms_service.send_sms('09384104825', 'این یک پیام تست از سیستم دکتر ترن است.')
        print(f"Basic SMS result: {result}")
        
        if result.get('success'):
            print("✅ Basic SMS sending works!")
        else:
            print(f"❌ Basic SMS failed: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Exception in basic SMS: {str(e)}")
    
    # Test 2: Verification code
    print("\n--- Testing Verification Code ---")
    try:
        result = sms_service.send_verification_code('09384104825')
        print(f"Verification code result: {result}")
        
        if result[1] == 200:  # success status
            print("✅ Verification code sending works!")
        else:
            print(f"❌ Verification code failed: {result[0]}")
            
    except Exception as e:
        print(f"❌ Exception in verification code: {str(e)}")
    
    # Test 3: Check SMS service configuration
    print("\n--- SMS Service Configuration ---")
    print(f"SMS Service Enabled: {sms_service.enabled}")
    print(f"API Key Configured: {bool(sms_service.api_key)}")
    print(f"Line Number Configured: {bool(sms_service.line_number)}")
    print(f"OTP Template ID: {sms_service.otp_template_id}")


def test_sms_with_mock_reservation():
    """Test SMS with a mock reservation object"""
    print("\n=== Testing SMS with Mock Reservation ===")
    
    # Create a mock reservation object
    class MockReservation:
        def __init__(self):
            self.id = 123
            self.patient = MockPatient()
            self.doctor = MockDoctor()
            self.day = MockReservationDay()
            self.time = MockTime()
    
    class MockPatient:
        def __init__(self):
            self.phone = '09384104825'
            self.name = 'علی احمدی'
    
    class MockDoctor:
        def __init__(self):
            self.user = MockUser()
    
    class MockUser:
        def get_full_name(self):
            return 'دکتر محمدی'
    
    class MockReservationDay:
        def __init__(self):
            self.date = MockDate()
    
    class MockTime:
        def strftime(self, format_str):
            return '10:00'
    
    class MockDate:
        def strftime(self, format_str):
            return '1403/01/15'
    
    # Create mock reservation
    mock_reservation = MockReservation()
    
    print(f"Mock Reservation ID: {mock_reservation.id}")
    print(f"Patient: {mock_reservation.patient.name}")
    print(f"Patient Phone: {mock_reservation.patient.phone}")
    print(f"Doctor: {mock_reservation.doctor.user.get_full_name()}")
    print(f"Date: {mock_reservation.day.date}")
    print(f"Time: {mock_reservation.time}")
    
    # Test 1: Confirmation SMS
    print("\n--- Testing Confirmation SMS with Mock ---")
    try:
        result = sms_service.send_appointment_confirmation(mock_reservation)
        print(f"Confirmation SMS result: {result}")
        
        if result.get('success'):
            print("✅ Confirmation SMS with mock works!")
        else:
            print(f"❌ Confirmation SMS with mock failed: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Exception in confirmation SMS with mock: {str(e)}")
    
    # Test 2: 24-hour reminder
    print("\n--- Testing 24-hour Reminder with Mock ---")
    try:
        result = sms_service.send_appointment_reminder(mock_reservation, 24)
        print(f"24h reminder result: {result}")
        
        if result.get('success'):
            print("✅ 24-hour reminder with mock works!")
        else:
            print(f"❌ 24-hour reminder with mock failed: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Exception in 24h reminder with mock: {str(e)}")
    
    # Test 3: Cancellation SMS
    print("\n--- Testing Cancellation SMS with Mock ---")
    try:
        result = sms_service.send_appointment_cancellation(mock_reservation)
        print(f"Cancellation SMS result: {result}")
        
        if result.get('success'):
            print("✅ Cancellation SMS with mock works!")
        else:
            print(f"❌ Cancellation SMS with mock failed: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Exception in cancellation SMS with mock: {str(e)}")


def main():
    """Main test function"""
    print("🚀 Simple SMS Service Test")
    print("=" * 50)
    
    # Test SMS service directly
    test_sms_service()
    
    # Test with mock reservation
    test_sms_with_mock_reservation()
    
    print("\n" + "=" * 50)
    print("✅ SMS service test completed!")
    print("💡 Check the results above to see if SMS functionality works correctly")


if __name__ == "__main__":
    main() 