from django.utils import timezone
from turn.models import Reservation, Reservation_Day
import datetime
from khayyam import JalaliDate
from . import holidays


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


def create_reservations(interval_minutes=10):
    today = timezone.now().date()
    holiday_dates = set(holidays.get_holidays())  # دریافت لیست تعطیلات رسمی از ماژول holidays

    for day_offset in range(18):
        reservation_date = today + datetime.timedelta(days=day_offset)
        jalali_date = JalaliDate(reservation_date)

        # رد کردن تعطیلات رسمی + پنج‌شنبه و جمعه
        if jalali_date.weekday() in [5, 6]:
            continue
        elif str(reservation_date) in holiday_dates:
            reservation_day, created = Reservation_Day.objects.get_or_create(date=reservation_date,published=False)
        else:
            reservation_day, created = Reservation_Day.objects.get_or_create(date=reservation_date)

        # زمان‌های نوبت صبح و عصر جداگانه
        morning_times = get_turn_times(9, 11, interval_minutes)  # نوبت‌های صبح از ۹ تا ۱۱
        evening_times = get_turn_times(15, 20, interval_minutes)  # نوبت‌های عصر از ۱۵ تا ۲۰
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
