"""
ابزارهای کمکی برای مدیریت رزرو نوبت
"""
from datetime import datetime, timedelta
from .models import ReservationDay
from doctors.holidays import get_holidays


class ReservationDayManager:
    """مدیریت روزهای رزرو"""
    
    @staticmethod
    def publish_days_for_range(start_date, end_date, exclude_holidays=True):
        """
        انتشار روزهای رزرو برای یک بازه زمانی
        
        Args:
            start_date: تاریخ شروع
            end_date: تاریخ پایان
            exclude_holidays: حذف تعطیلات رسمی
        
        Returns:
            tuple: (days_published, days_updated)
        """
        days_published = 0
        days_updated = 0
        
        # دریافت تعطیلات رسمی
        holidays = set()
        if exclude_holidays:
            try:
                holidays = set(get_holidays())
            except Exception:
                # در صورت خطا، بدون تعطیلات ادامه بده
                pass
        
        current_date = start_date
        
        while current_date <= end_date:
            # بررسی تعطیل بودن
            is_holiday = current_date in holidays
            
            # ایجاد یا بروزرسانی روز رزرو
            reservation_day, created = ReservationDay.objects.get_or_create(
                date=current_date,
                defaults={'published': not is_holiday}
            )
            
            if created:
                days_published += 1
            else:
                # بروزرسانی وضعیت انتشار
                old_published = reservation_day.published
                reservation_day.published = not is_holiday
                reservation_day.save()
                
                if old_published != reservation_day.published:
                    days_updated += 1
            
            current_date += timedelta(days=1)
        
        return days_published, days_updated
    
    @staticmethod
    def unpublish_specific_dates(dates):
        """
        عدم انتشار تاریخ‌های مشخص
        
        Args:
            dates: لیست تاریخ‌ها
        
        Returns:
            int: تعداد روزهای غیرفعال شده
        """
        updated_count = 0
        
        for date in dates:
            try:
                reservation_day = ReservationDay.objects.get(date=date)
                if reservation_day.published:
                    reservation_day.published = False
                    reservation_day.save()
                    updated_count += 1
            except ReservationDay.DoesNotExist:
                # اگر روز وجود نداشت، ایجاد کن
                ReservationDay.objects.create(date=date, published=False)
                updated_count += 1
        
        return updated_count
    
    @staticmethod
    def publish_specific_dates(dates):
        """
        انتشار تاریخ‌های مشخص
        
        Args:
            dates: لیست تاریخ‌ها
        
        Returns:
            int: تعداد روزهای فعال شده
        """
        updated_count = 0
        
        for date in dates:
            reservation_day, created = ReservationDay.objects.get_or_create(
                date=date,
                defaults={'published': True}
            )
            
            if created:
                updated_count += 1
            elif not reservation_day.published:
                reservation_day.published = True
                reservation_day.save()
                updated_count += 1
        
        return updated_count
    
    @staticmethod
    def get_published_days_count(start_date=None, end_date=None):
        """
        شمارش روزهای منتشر شده
        
        Args:
            start_date: تاریخ شروع (اختیاری)
            end_date: تاریخ پایان (اختیاری)
        
        Returns:
            int: تعداد روزهای منتشر شده
        """
        queryset = ReservationDay.objects.filter(published=True)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.count()
    
    @staticmethod
    def cleanup_old_days(days_before=90):
        """
        پاک‌سازی روزهای قدیمی
        
        Args:
            days_before: تعداد روزهای قبل از امروز برای پاک‌سازی
        
        Returns:
            int: تعداد روزهای پاک شده
        """
        cutoff_date = datetime.now().date() - timedelta(days=days_before)
        deleted_count, _ = ReservationDay.objects.filter(
            date__lt=cutoff_date
        ).delete()
        
        return deleted_count


def format_persian_date_range(start_date, end_date):
    """
    فرمت‌بندی بازه تاریخ به شمسی
    
    Args:
        start_date: تاریخ شروع
        end_date: تاریخ پایان
    
    Returns:
        str: بازه تاریخ فرمت شده
    """
    import jdatetime
    
    start_jalali = jdatetime.date.fromgregorian(date=start_date)
    end_jalali = jdatetime.date.fromgregorian(date=end_date)
    
    if start_date.year == end_date.year:
        if start_date.month == end_date.month:
            return f"{start_jalali.day} تا {end_jalali.day} {start_jalali.strftime('%B %Y')}"
        else:
            return f"{start_jalali.strftime('%d %B')} تا {end_jalali.strftime('%d %B %Y')}"
    else:
        return f"{start_jalali.strftime('%Y/%m/%d')} تا {end_jalali.strftime('%Y/%m/%d')}" 