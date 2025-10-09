"""
ابزار ایجاد روزهای حضور پزشک و نوبت‌های رزرو بر اساس زمان‌بندی هفتگی
"""
import jdatetime
from datetime import datetime, timedelta, time
from django.utils import timezone
from django.db import transaction
from .models import ReservationDay, Reservation
from .utils import ReservationDayManager
from .holidays import get_holidays


def get_turn_times(start_time, end_time, interval_minutes):
    """تولید لیست زمان‌های نوبت با فاصله مشخص"""
    times = []
    current_time = start_time
    
    # تبدیل زمان پایان به دقیقه
    end_minutes = end_time.hour * 60 + end_time.minute
    
    while True:
        # تبدیل زمان جاری به دقیقه
        current_minutes = current_time.hour * 60 + current_time.minute
        
        if current_minutes >= end_minutes:
            break
            
        times.append(current_time)
        
        # اضافه کردن فاصله زمانی
        new_minutes = current_minutes + interval_minutes
        new_hour = new_minutes // 60
        new_minute = new_minutes % 60
        
        # جلوگیری از overflow
        if new_hour >= 24:
            break
            
        current_time = time(new_hour, new_minute)
    
    return times


@transaction.atomic
def create_availability_days_and_slots_for_day_of_week(doctor, day_of_week, start_time, end_time):
    """
    ایجاد روزهای حضور و نوبت‌های رزرو برای یک روز مشخص از هفته در طول سال
    
    Args:
        doctor: نمونه پزشک
        day_of_week: روز هفته (0=شنبه، 6=جمعه)
        start_time: زمان شروع
        end_time: زمان پایان
    
    Returns:
        dict: آمار ایجاد شده
    """
    # تاریخ‌های شروع و پایان (سال جاری تا سال آینده)
    current_jalali = jdatetime.date.today()
    start_jalali = jdatetime.date(current_jalali.year, 1, 1)  # اول فروردین سال جاری
    end_jalali = jdatetime.date(current_jalali.year + 1, 12, 29)  # آخر اسفند سال آینده
    
    # تبدیل به میلادی
    start_date = start_jalali.togregorian()
    end_date = end_jalali.togregorian()
    
    # پیدا کردن تمام تاریخ‌هایی که با روز هفته مطابقت دارند
    target_dates = []
    current_date = start_date
    
    while current_date <= end_date:
        # تبدیل تاریخ میلادی به روز هفته (0=شنبه، 6=جمعه)
        gregorian_day_of_week = current_date.weekday()
        persian_day_of_week = (gregorian_day_of_week + 2) % 7
        
        if persian_day_of_week == day_of_week:
            target_dates.append(current_date)
        
        current_date += timedelta(days=1)
    
    # دریافت تعطیلات رسمی
    try:
        holidays = set(get_holidays())
    except Exception:
        holidays = set()
    
    # تولید زمان‌های نوبت
    slot_times = get_turn_times(start_time, end_time, doctor.consultation_duration)
    
    # آمارگیری
    days_created = 0
    days_updated = 0
    days_skipped_holiday = 0
    reservations_created = 0
    reservations_updated = 0
    
    # ایجاد یا بروزرسانی روزهای حضور و نوبت‌ها
    for date in target_dates:
        is_holiday = date in holidays
        
        # ایجاد یا بروزرسانی روز رزرو
        reservation_day, day_created = ReservationDay.objects.get_or_create(
            date=date,
            defaults={'published': not is_holiday}
        )
        
        if day_created:
            if is_holiday:
                days_skipped_holiday += 1
            else:
                days_created += 1
        else:
            # بروزرسانی وضعیت انتشار
            old_published = reservation_day.published
            new_published = not is_holiday
            
            if old_published != new_published:
                reservation_day.published = new_published
                reservation_day.save()
                days_updated += 1
                
                if is_holiday:
                    days_skipped_holiday += 1
        
        # ایجاد نوبت‌های رزرو فقط اگر روز منتشر شده باشد
        if reservation_day.published:
            for slot_time in slot_times:
                # بررسی وجود نوبت قبلی
                reservation, res_created = Reservation.objects.get_or_create(
                    day=reservation_day,
                    doctor=doctor,
                    time=slot_time,
                    defaults={
                        'phone': '',  # خالی - پر می‌شود هنگام رزرو
                        'amount': doctor.consultation_fee,
                        'status': 'available',  # وضعیت جدید برای نوبت‌های آزاد
                        'payment_status': 'pending'
                    }
                )
                
                if res_created:
                    reservations_created += 1
                else:
                    # بروزرسانی مبلغ در صورت تغییر تعرفه پزشک
                    if reservation.amount != doctor.consultation_fee and reservation.status == 'available':
                        reservation.amount = doctor.consultation_fee
                        reservation.save()
                        reservations_updated += 1
    
    return {
        'days_created': days_created,
        'days_updated': days_updated,
        'days_skipped_holiday': days_skipped_holiday,
        'reservations_created': reservations_created,
        'reservations_updated': reservations_updated,
        'total_dates_processed': len(target_dates),
        'total_slot_times': len(slot_times),
        'date_range': f"{start_date} تا {end_date}"
    }


def create_availability_days_for_day_of_week(doctor, day_of_week, start_time, end_time):
    """
    نسخه سازگار با قبل - فقط ایجاد روزهای حضور (بدون نوبت‌ها)
    """
    return create_availability_days_and_slots_for_day_of_week(doctor, day_of_week, start_time, end_time)


@transaction.atomic
def regenerate_doctor_reservations(doctor):
    """
    بازتولید کامل نوبت‌های یک پزشک بر اساس زمان‌بندی‌های فعلی
    
    Args:
        doctor: نمونه پزشک
    
    Returns:
        dict: آمار عملیات
    """
    total_stats = {
        'days_created': 0,
        'days_updated': 0,
        'days_skipped_holiday': 0,
        'reservations_created': 0,
        'reservations_updated': 0,
        'availabilities_processed': 0
    }
    
    # پردازش تمام زمان‌بندی‌های پزشک
    availabilities = doctor.availabilities.all()
    
    for availability in availabilities:
        stats = create_availability_days_and_slots_for_day_of_week(
            doctor=doctor,
            day_of_week=availability.day_of_week,
            start_time=availability.start_time,
            end_time=availability.end_time
        )
        
        # جمع آوری آمار
        for key in ['days_created', 'days_updated', 'days_skipped_holiday', 
                   'reservations_created', 'reservations_updated']:
            total_stats[key] += stats.get(key, 0)
        
        total_stats['availabilities_processed'] += 1
    
    return total_stats


@transaction.atomic
def update_doctor_availability_slots(doctor, day_of_week, old_start_time, old_end_time, new_start_time, new_end_time):
    """
    بروزرسانی نوبت‌های موجود هنگام تغییر زمان‌بندی پزشک
    
    Args:
        doctor: نمونه پزشک
        day_of_week: روز هفته
        old_start_time: زمان شروع قبلی
        old_end_time: زمان پایان قبلی
        new_start_time: زمان شروع جدید
        new_end_time: زمان پایان جدید
    
    Returns:
        dict: آمار تغییرات
    """
    # تولید زمان‌های قدیمی و جدید
    old_slots = get_turn_times(old_start_time, old_end_time, doctor.consultation_duration)
    new_slots = get_turn_times(new_start_time, new_end_time, doctor.consultation_duration)
    
    old_slots_set = set(old_slots)
    new_slots_set = set(new_slots)
    
    # پیدا کردن تغییرات
    slots_to_remove = old_slots_set - new_slots_set
    slots_to_add = new_slots_set - old_slots_set
    
    removed_count = 0
    added_count = 0
    
    # پیدا کردن تمام روزهای مطابق با day_of_week
    today = datetime.now().date()
    future_date = today + timedelta(days=365)  # یک سال آینده
    
    current_date = today
    while current_date <= future_date:
        gregorian_day_of_week = current_date.weekday()
        persian_day_of_week = (gregorian_day_of_week + 2) % 7
        
        if persian_day_of_week == day_of_week:
            try:
                reservation_day = ReservationDay.objects.get(date=current_date, published=True)
                
                # حذف نوبت‌های غیرضروری (فقط اگر رزرو نشده‌اند)
                for slot_time in slots_to_remove:
                    deleted = Reservation.objects.filter(
                        day=reservation_day,
                        doctor=doctor,
                        time=slot_time,
                        status='available'
                    ).delete()
                    removed_count += deleted[0]
                
                # اضافه کردن نوبت‌های جدید
                for slot_time in slots_to_add:
                    reservation, created = Reservation.objects.get_or_create(
                        day=reservation_day,
                        doctor=doctor,
                        time=slot_time,
                        defaults={
                            'phone': '',
                            'amount': doctor.consultation_fee,
                            'status': 'available',
                            'payment_status': 'pending'
                        }
                    )
                    if created:
                        added_count += 1
                        
            except ReservationDay.DoesNotExist:
                continue
        
        current_date += timedelta(days=1)
    
    return {
        'slots_removed': removed_count,
        'slots_added': added_count,
        'old_slots_count': len(old_slots),
        'new_slots_count': len(new_slots)
    }


def create_availability_for_date_range(doctor, start_date, end_date, days_of_week=None):
    """
    ایجاد روزهای حضور برای یک بازه زمانی مشخص
    
    Args:
        doctor: نمونه پزشک
        start_date: تاریخ شروع
        end_date: تاریخ پایان
        days_of_week: لیست روزهای هفته (اختیاری) - اگر None باشد از availabilities پزشک استفاده می‌شود
    
    Returns:
        dict: آمار ایجاد شده
    """
    if days_of_week is None:
        # استفاده از زمان‌بندی موجود پزشک
        doctor_availabilities = doctor.availabilities.all()
        days_of_week = [av.day_of_week for av in doctor_availabilities]
    
    # استفاده از ReservationDayManager برای ایجاد کلی
    days_published, days_updated = ReservationDayManager.publish_days_for_range(
        start_date, end_date, exclude_holidays=True
    )
    
    # فیلتر کردن فقط روزهایی که پزشک دردسترس است
    total_filtered = 0
    current_date = start_date
    
    while current_date <= end_date:
        gregorian_day_of_week = current_date.weekday()
        persian_day_of_week = (gregorian_day_of_week + 2) % 7
        
        if persian_day_of_week not in days_of_week:
            # غیرفعال کردن روزهایی که پزشک دردسترس نیست
            try:
                reservation_day = ReservationDay.objects.get(date=current_date)
                if reservation_day.published:
                    reservation_day.published = False
                    reservation_day.save()
                    total_filtered += 1
            except ReservationDay.DoesNotExist:
                pass
        
        current_date += timedelta(days=1)
    
    return {
        'days_published': days_published,
        'days_updated': days_updated,
        'days_filtered': total_filtered,
        'doctor_available_days': days_of_week
    }


def create_reservations(interval_minutes=10):
    today = timezone.now().date()
    holiday_dates = set(holidays.get_holidays())  # دریافت لیست تعطیلات رسمی از ماژول holidays

    for day_offset in range(395):
        reservation_date = today + datetime.timedelta(days=day_offset)
        jalali_date = JalaliDate(reservation_date)

        # رد کردن تعطیلات رسمی + پنج‌شنبه و جمعه
        if jalali_date.weekday() in [5, 6]:
            continue
        elif str(reservation_date) in holiday_dates:
            reservation_day, created = ReservationDay.objects.get_or_create(date=reservation_date,published=False)
        else:
            reservation_day, created = ReservationDay.objects.get_or_create(date=reservation_date)

        # زمان‌های نوبت صبح و عصر جداگانه
        morning_times = get_turn_times(9, 11, interval_minutes)
        evening_times = get_turn_times(15, 20, interval_minutes)
        turn_times = morning_times + evening_times

        # گرفتن همه رزروهای روز جاری برای کاهش تعداد کوئری‌ها
        existing_turns = set(Reservation.objects.filter(day=reservation_day).values_list('time', flat=True))

        # ایجاد نوبت‌های جدید فقط در صورتی که وجود نداشته باشند
        new_reservations = [
            Reservation(day=reservation_day, time=turn_time)
            for turn_time in turn_times if turn_time not in existing_turns
        ]

        if new_reservations:
            Reservation.objects.bulk_create(new_reservations)  # استفاده از bulk_create برای بهینه‌سازی
