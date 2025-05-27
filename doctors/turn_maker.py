"""
ابزار ایجاد روزهای حضور پزشک بر اساس زمان‌بندی هفتگی
"""
import jdatetime
from datetime import datetime, timedelta
from django.utils import timezone
from reservations.models import ReservationDay
from reservations.utils import ReservationDayManager
from .holidays import get_holidays


def get_turn_times(start_hour, end_hour, interval_minutes):
    """تولید لیست زمان‌های نوبت با فاصله مشخص"""
    times = []
    current_time = datetime.time(start_hour, 0)
    end_time = datetime.time(end_hour, 0)

    while current_time < end_time:
        times.append(current_time)
        current_time = (datetime.datetime.combine(datetime.date.today(), current_time) +
                        datetime.timedelta(minutes=interval_minutes)).time()

    return times


def create_availability_days_for_day_of_week(doctor, day_of_week, start_time, end_time):
    """
    ایجاد روزهای حضور برای یک روز مشخص از هفته در طول سال
    
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
    
    # آمارگیری
    days_created = 0
    days_updated = 0
    days_skipped_holiday = 0
    
    # ایجاد یا بروزرسانی روزهای حضور
    for date in target_dates:
        is_holiday = date in holidays
        
        # ایجاد یا بروزرسانی روز رزرو
        reservation_day, created = ReservationDay.objects.get_or_create(
            date=date,
            defaults={'published': not is_holiday}
        )
        
        if created:
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
    
    return {
        'days_created': days_created,
        'days_updated': days_updated,
        'days_skipped_holiday': days_skipped_holiday,
        'total_dates_processed': len(target_dates),
        'date_range': f"{start_date} تا {end_date}"
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
