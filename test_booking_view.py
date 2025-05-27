#!/usr/bin/env python
"""
تست view رزرو نوبت
"""

import os
import django
import sys
from datetime import datetime, time, date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dr_turn.settings')
django.setup()

from django.test import Client, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from doctors.models import Doctor, DoctorAvailability, Specialization, City
from reservations.models import ReservationDay, Reservation
from reservations.views import book_appointment
from reservations.services import BookingService

User = get_user_model()

def test_booking_view():
    """تست view رزرو نوبت"""
    print("🔧 تست view رزرو نوبت")
    print("=" * 40)
    
    # ایجاد کاربر و پزشک
    user, created = User.objects.get_or_create(
        phone='09123456789',
        defaults={
            'email': 'doctor@test.com',
            'first_name': 'دکتر',
            'last_name': 'تست',
        }
    )
    
    city, _ = City.objects.get_or_create(name='تهران')
    specialization, _ = Specialization.objects.get_or_create(name='پزشک عمومی')
    
    doctor, _ = Doctor.objects.get_or_create(
        user=user,
        defaults={
            'specialization': specialization,
            'license_number': '12345',
            'city': city,
            'bio': 'پزشک تست',
            'consultation_fee': 50000,
            'is_available': True,
        }
    )
    
    print(f"✓ پزشک: {doctor}")
    
    # ایجاد کاربر بیمار
    patient_user, _ = User.objects.get_or_create(
        phone='09987654321',
        defaults={
            'email': 'patient@test.com',
            'first_name': 'بیمار',
            'last_name': 'تست',
        }
    )
    print(f"✓ بیمار: {patient_user}")
    
    # ایجاد client
    client = Client()
    client.force_login(patient_user)
    
    # تست GET request
    print("\n--- تست GET request ---")
    response = client.get(f'/reservations/book/{doctor.id}/')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ صفحه رزرو با موفقیت بارگذاری شد")
        
        # Check HTML content instead of context
        content = response.content.decode('utf-8')
        
        # Check if doctor name is in the content
        if doctor.user.first_name in content or str(doctor) in content:
            print(f"✓ پزشک در صفحه: {doctor}")
        else:
            print("❌ پزشک در صفحه یافت نشد")
            
        # Check if form exists
        if 'name="date"' in content and 'name="time"' in content:
            print("✓ فرم رزرو در صفحه موجود است")
        else:
            print("❌ فرم رزرو در صفحه یافت نشد")
            
        # Check if there are available slots
        if 'انتخاب تاریخ' in content:
            print("✓ فیلد انتخاب تاریخ موجود است")
        else:
            print("❌ فیلد انتخاب تاریخ یافت نشد")
            
    else:
        print(f"❌ خطا در بارگذاری صفحه: {response.status_code}")
        print(f"Response content: {response.content}")
        return
    
    # پیدا کردن یک اسلات موجود برای تست POST
    print("\n--- پیدا کردن اسلات موجود ---")
    booking_service = BookingService()
    
    try:
        available_days = booking_service.get_available_days_for_doctor(doctor.id, days_ahead=30)
        
        if available_days:
            first_day = available_days[0]
            print(f"✓ روز موجود: {first_day['jalali_date']}")
            
            if first_day['slots']:
                first_slot = first_day['slots'][0]
                test_date = first_day['jalali_date']
                test_time = first_slot.strftime('%H:%M')
                print(f"✓ اسلات موجود: {test_time}")
                
                # Test POST request
                print("\n--- تست POST request ---")
                post_data = {
                    'date': test_date,
                    'time': test_time,
                    'patient_name': 'بیمار تست',
                    'phone': '09987654321',
                    'patient_national_id': '1234567890',
                    'patient_email': 'test@example.com'
                }
                
                response = client.post(f'/reservations/book/{doctor.id}/', post_data)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 302:
                    print("✓ رزرو با موفقیت انجام شد (redirect)")
                    print(f"Redirect URL: {response.url}")
                elif response.status_code == 200:
                    print("❌ رزرو انجام نشد - صفحه دوباره نمایش داده شد")
                    content = response.content.decode('utf-8')
                    if 'خطا' in content or 'error' in content:
                        print("❌ خطا در رزرو")
                else:
                    print(f"❌ خطای غیرمنتظره: {response.status_code}")
            else:
                print("❌ اسلات موجود یافت نشد")
        else:
            print("❌ روز موجود یافت نشد")
            
    except Exception as e:
        print(f"❌ خطا در دریافت اسلات‌ها: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 40)
    print("✅ تست تکمیل شد")

if __name__ == '__main__':
    test_booking_view() 