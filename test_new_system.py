#!/usr/bin/env python
"""
تست سیستم جدید رزرو نوبت با ایجاد خودکار اسلات‌ها
"""

import os
import django
import sys
from datetime import datetime, time, date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dr_turn.settings')
django.setup()

from django.contrib.auth import get_user_model
from doctors.models import Doctor, DoctorAvailability, Specialization, City
from reservations.models import ReservationDay, Reservation
from reservations.turn_maker import (
    create_availability_days_and_slots_for_day_of_week,
    get_turn_times,
    regenerate_doctor_reservations
)
from reservations.services import BookingService

User = get_user_model()

def create_test_data():
    """ایجاد داده‌های تست"""
    print("=== ایجاد داده‌های تست ===")
    
    # ایجاد کاربر پزشک
    user, created = User.objects.get_or_create(
        phone='09123456789',
        defaults={
            'email': 'doctor@test.com',
            'first_name': 'دکتر',
            'last_name': 'تست',
        }
    )
    print(f"کاربر پزشک: {'ایجاد' if created else 'موجود'}")
    
    # ایجاد شهر
    city, created = City.objects.get_or_create(
        name='تهران'
    )
    print(f"شهر: {'ایجاد' if created else 'موجود'}")
    
    # ایجاد تخصص
    specialization, created = Specialization.objects.get_or_create(
        name='پزشک عمومی'
    )
    print(f"تخصص: {'ایجاد' if created else 'موجود'}")
    
    # ایجاد پزشک
    doctor, created = Doctor.objects.get_or_create(
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
    print(f"پزشک: {'ایجاد' if created else 'موجود'}")
    
    return doctor, user

def test_availability_creation():
    """تست ایجاد زمان‌بندی و اسلات‌ها"""
    print("\n=== تست ایجاد زمان‌بندی ===")
    
    doctor, user = create_test_data()
    
    # پاک کردن زمان‌بندی‌های قبلی
    doctor.availabilities.all().delete()
    print("زمان‌بندی‌های قبلی پاک شد")
    
    # ایجاد زمان‌بندی جدید
    availability1 = DoctorAvailability.objects.create(
        doctor=doctor,
        day_of_week=0,  # شنبه
        start_time=time(8, 0),
        end_time=time(12, 0)
    )
    
    availability2 = DoctorAvailability.objects.create(
        doctor=doctor,
        day_of_week=2,  # دوشنبه
        start_time=time(14, 0),
        end_time=time(18, 0)
    )
    
    print(f"زمان‌بندی ایجاد شد:")
    print(f"  - شنبه: 08:00-12:00")
    print(f"  - دوشنبه: 14:00-18:00")
    
    # بررسی ایجاد خودکار اسلات‌ها
    today = date.today()
    next_month = today + timedelta(days=30)
    
    reservation_days = ReservationDay.objects.filter(
        date__gte=today,
        date__lte=next_month
    ).count()
    
    reservations = Reservation.objects.filter(
        doctor=doctor,
        status='available',
        day__date__gte=today,
        day__date__lte=next_month
    ).count()
    
    print(f"\nنتایج:")
    print(f"  - روزهای رزرو ایجاد شده: {reservation_days}")
    print(f"  - اسلات‌های موجود: {reservations}")
    
    return doctor, user

def test_booking_service():
    """تست سرویس رزرو"""
    print("\n=== تست سرویس رزرو ===")
    
    doctor, user = test_availability_creation()
    
    booking_service = BookingService()
    
    # دریافت روزهای موجود
    available_days = booking_service.get_available_days_for_doctor(doctor.id, days_ahead=30)
    print(f"روزهای موجود: {len(available_days)}")
    
    if available_days:
        first_day = available_days[0]
        print(f"اولین روز موجود: {first_day['jalali_date']} - {len(first_day['slots'])} اسلات")
        
        # دریافت اسلات‌های موجود
        slots = doctor.get_available_slots(first_day['date'])
        print(f"اسلات‌های موجود برای {first_day['jalali_date']}: {len(slots)}")
        for slot in slots[:3]:  # نمایش 3 اسلات اول
            print(f"  - {slot}")
    
    return doctor, user

def test_manual_booking():
    """تست رزرو دستی"""
    print("\n=== تست رزرو دستی ===")
    
    doctor, user = test_booking_service()
    
    # ایجاد کاربر بیمار
    patient_user, created = User.objects.get_or_create(
        phone='09987654321',
        defaults={
            'email': 'patient@test.com',
            'first_name': 'بیمار',
            'last_name': 'تست',
        }
    )
    print(f"کاربر بیمار: {'ایجاد' if created else 'موجود'}")
    
    # پیدا کردن اولین اسلات موجود
    available_reservation = Reservation.objects.filter(
        doctor=doctor,
        status='available'
    ).first()
    
    if available_reservation:
        print(f"رزرو اسلات: {available_reservation.day.date} - {available_reservation.time}")
        
        # رزرو کردن
        patient_data = {
            'name': 'بیمار تست',
            'phone': '09987654321',
            'national_id': '1234567890',
            'email': 'patient@test.com'
        }
        
        success, message = available_reservation.book_appointment(
            patient_data=patient_data,
            user=patient_user
        )
        
        if success:
            print("✓ رزرو با موفقیت انجام شد")
            print(f"وضعیت: {available_reservation.get_status_display()}")
        else:
            print(f"❌ خطا در رزرو: {message}")
    else:
        print("❌ هیچ اسلات موجودی یافت نشد")
    
    return doctor, user

def test_regenerate_slots():
    """تست بازتولید اسلات‌ها"""
    print("\n=== تست بازتولید اسلات‌ها ===")
    
    doctor, user = test_manual_booking()
    
    # شمارش اسلات‌های قبلی
    before_count = Reservation.objects.filter(doctor=doctor).count()
    print(f"تعداد اسلات‌ها قبل از بازتولید: {before_count}")
    
    # بازتولید اسلات‌ها
    stats = regenerate_doctor_reservations(doctor)
    
    print(f"آمار بازتولید:")
    print(f"  - زمان‌بندی‌های پردازش شده: {stats['availabilities_processed']}")
    print(f"  - روزهای ایجاد شده: {stats['days_created']}")
    print(f"  - نوبت‌های ایجاد شده: {stats['reservations_created']}")
    
    # شمارش اسلات‌های بعدی
    after_count = Reservation.objects.filter(doctor=doctor).count()
    print(f"تعداد اسلات‌ها بعد از بازتولید: {after_count}")
    
    return doctor, user

def test_cleanup():
    """پاک‌سازی داده‌های تست"""
    print("\n=== پاک‌سازی ===")
    
    # پاک کردن رزروها
    deleted_reservations = Reservation.objects.all().delete()[0]
    print(f"رزروهای پاک شده: {deleted_reservations}")
    
    # پاک کردن روزهای رزرو
    deleted_days = ReservationDay.objects.all().delete()[0]
    print(f"روزهای رزرو پاک شده: {deleted_days}")
    
    # پاک کردن زمان‌بندی‌ها
    deleted_availabilities = DoctorAvailability.objects.all().delete()[0]
    print(f"زمان‌بندی‌های پاک شده: {deleted_availabilities}")

def main():
    """اجرای تست‌ها"""
    print("🏥 تست سیستم رزرو نوبت جدید")
    print("=" * 50)
    
    try:
        test_availability_creation()
        test_booking_service()
        test_manual_booking()
        test_regenerate_slots()
        
        print("\n" + "=" * 50)
        print("✅ همه تست‌ها با موفقیت انجام شد!")
        
        # آیا پاک‌سازی انجام شود؟
        cleanup = input("\nآیا داده‌های تست پاک شوند؟ (y/N): ").lower().strip()
        if cleanup == 'y':
            test_cleanup()
            print("✓ پاک‌سازی تکمیل شد")
        else:
            print("داده‌های تست حفظ شدند")
            
    except Exception as e:
        print(f"\n❌ خطا در تست: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main() 