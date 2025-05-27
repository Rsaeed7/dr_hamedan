"""
Management command for managing doctor availability days
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
import jdatetime

from doctors.models import Doctor, DoctorAvailability
from reservations.models import ReservationDay
from doctors.turn_maker import create_availability_days_for_day_of_week
from doctors.holidays import get_holidays


class Command(BaseCommand):
    help = 'مدیریت روزهای حضور پزشکان'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['create-days', 'create-range', 'publish-range', 'unpublish-dates', 'cleanup'],
            help='عمل مورد نظر'
        )
        
        parser.add_argument(
            '--doctor-id',
            type=int,
            help='شناسه پزشک (اختیاری - اگر مشخص نشود، برای همه پزشکان اعمال می‌شود)'
        )
        
        parser.add_argument(
            '--day-of-week',
            type=int,
            choices=range(0, 7),
            help='روز هفته (0=دوشنبه، 6=یکشنبه) برای ایجاد روزهای حضور'
        )
        
        parser.add_argument(
            '--start-date',
            type=str,
            help='تاریخ شروع (فرمت: YYYY-MM-DD)'
        )
        
        parser.add_argument(
            '--end-date',
            type=str,
            help='تاریخ پایان (فرمت: YYYY-MM-DD)'
        )
        
        parser.add_argument(
            '--dates',
            type=str,
            nargs='+',
            help='لیست تاریخ‌های مشخص (فرمت: YYYY-MM-DD)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='نمایش تغییرات بدون اعمال آن‌ها'
        )

    def handle(self, *args, **options):
        action = options['action']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('حالت آزمایشی - هیچ تغییری اعمال نخواهد شد')
            )
        
        try:
            if action == 'create-days':
                self.create_availability_days(options, dry_run)
            elif action == 'create-range':
                self.create_date_range(options, dry_run)
            elif action == 'publish-range':
                self.publish_date_range(options, dry_run)
            elif action == 'unpublish-dates':
                self.unpublish_dates(options, dry_run)
            elif action == 'cleanup':
                self.cleanup_old_days(options, dry_run)
                
        except Exception as e:
            raise CommandError(f'خطا در اجرای دستور: {str(e)}')

    def create_availability_days(self, options, dry_run):
        """ایجاد روزهای حضور برای روز مشخص هفته"""
        doctor_id = options.get('doctor_id')
        day_of_week = options.get('day_of_week')
        
        if day_of_week is None:
            raise CommandError('روز هفته باید مشخص شود (--day-of-week)')
        
        # دریافت پزشکان
        if doctor_id:
            try:
                doctors = [Doctor.objects.get(id=doctor_id)]
            except Doctor.DoesNotExist:
                raise CommandError(f'پزشک با شناسه {doctor_id} یافت نشد')
        else:
            doctors = Doctor.objects.filter(is_available=True)
        
        total_days_created = 0
        total_days_updated = 0
        
        for doctor in doctors:
            self.stdout.write(f'پردازش پزشک: {doctor.user.get_full_name()}')
            
            # دریافت تنظیمات حضور پزشک
            availabilities = doctor.availabilities.filter(day_of_week=day_of_week)
            
            if not availabilities.exists():
                self.stdout.write(
                    self.style.WARNING(f'  هیچ تنظیم حضوری برای روز {day_of_week} یافت نشد')
                )
                continue
            
            for availability in availabilities:
                if not dry_run:
                    result = create_availability_days_for_day_of_week(
                        doctor, availability.day_of_week, availability.start_time, availability.end_time
                    )
                    total_days_created += result['days_created']
                    total_days_updated += result['days_updated']
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ایجاد شد: {result["days_created"]} روز، بروزرسانی شد: {result["days_updated"]} روز، '
                            f'تعطیل رد شد: {result["days_skipped_holiday"]} روز'
                        )
                    )
                else:
                    self.stdout.write(
                        f'  خواهد شد: ایجاد روزهای حضور برای {availability.get_day_of_week_display()} '
                        f'از {availability.start_time} تا {availability.end_time}'
                    )
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'مجموع: {total_days_created} روز ایجاد شد، {total_days_updated} روز بروزرسانی شد'
                )
            )

    def create_date_range(self, options, dry_run):
        """ایجاد روزهای رزرو برای بازه تاریخی"""
        start_date = options.get('start_date')
        end_date = options.get('end_date')
        
        if not start_date or not end_date:
            raise CommandError('تاریخ شروع و پایان باید مشخص شود')
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            raise CommandError('فرمت تاریخ نامعتبر است (YYYY-MM-DD)')
        
        if start_date > end_date:
            raise CommandError('تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد')
        
        # دریافت تعطیلات
        holidays = get_holidays()
        holiday_dates = [holiday['date'] for holiday in holidays]
        
        current_date = start_date
        days_created = 0
        days_skipped = 0
        
        while current_date <= end_date:
            # بررسی تعطیل بودن
            if current_date in holiday_dates:
                days_skipped += 1
                self.stdout.write(
                    self.style.WARNING(f'رد شد (تعطیل): {current_date}')
                )
            else:
                if not dry_run:
                    day, created = ReservationDay.objects.get_or_create(
                        date=current_date,
                        defaults={'published': False}
                    )
                    if created:
                        days_created += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'ایجاد شد: {current_date}')
                        )
                    else:
                        self.stdout.write(f'موجود: {current_date}')
                else:
                    self.stdout.write(f'خواهد شد: ایجاد {current_date}')
                    days_created += 1
            
            current_date += timedelta(days=1)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'مجموع: {days_created} روز ایجاد شد، {days_skipped} روز رد شد'
            )
        )

    def publish_date_range(self, options, dry_run):
        """انتشار روزهای رزرو در بازه تاریخی"""
        start_date = options.get('start_date')
        end_date = options.get('end_date')
        
        if not start_date or not end_date:
            raise CommandError('تاریخ شروع و پایان باید مشخص شود')
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            raise CommandError('فرمت تاریخ نامعتبر است (YYYY-MM-DD)')
        
        days = ReservationDay.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            published=False
        )
        
        count = days.count()
        
        if not dry_run:
            days.update(published=True)
            self.stdout.write(
                self.style.SUCCESS(f'{count} روز منتشر شد')
            )
        else:
            self.stdout.write(f'خواهد شد: انتشار {count} روز')

    def unpublish_dates(self, options, dry_run):
        """لغو انتشار تاریخ‌های مشخص"""
        dates = options.get('dates')
        
        if not dates:
            raise CommandError('لیست تاریخ‌ها باید مشخص شود (--dates)')
        
        parsed_dates = []
        for date_str in dates:
            try:
                parsed_dates.append(datetime.strptime(date_str, '%Y-%m-%d').date())
            except ValueError:
                raise CommandError(f'فرمت تاریخ نامعتبر: {date_str}')
        
        days = ReservationDay.objects.filter(
            date__in=parsed_dates,
            published=True
        )
        
        count = days.count()
        
        if not dry_run:
            days.update(published=False)
            self.stdout.write(
                self.style.SUCCESS(f'{count} روز لغو انتشار شد')
            )
        else:
            self.stdout.write(f'خواهد شد: لغو انتشار {count} روز')

    def cleanup_old_days(self, options, dry_run):
        """پاک‌سازی روزهای قدیمی"""
        cutoff_date = timezone.now().date() - timedelta(days=30)
        
        old_days = ReservationDay.objects.filter(
            date__lt=cutoff_date,
            published=False
        )
        
        count = old_days.count()
        
        if not dry_run:
            old_days.delete()
            self.stdout.write(
                self.style.SUCCESS(f'{count} روز قدیمی پاک شد')
            )
        else:
            self.stdout.write(f'خواهد شد: پاک‌سازی {count} روز قدیمی') 