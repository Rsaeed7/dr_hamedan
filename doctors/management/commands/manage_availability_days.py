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
from doctors.turn_maker import create_availability_days_and_slots_for_day_of_week
from doctors.holidays import get_holidays


class Command(BaseCommand):
    help = 'مدیریت روزهای حضور پزشکان'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['create-days', 'create-range', 'generate-doctor-slots', 'publish-range', 'unpublish-dates', 'cleanup'],
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
        """اجرای دستور"""
        action = options['action']
        
        try:
            if action == 'create-days':
                return self.handle_create_days(options)
            elif action == 'create-range':
                return self.handle_create_range(options)
            elif action == 'generate-doctor-slots':
                return self.handle_generate_doctor_slots(options)
            elif action == 'publish-range':
                return self.handle_publish_range(options)
            elif action == 'unpublish-dates':
                return self.handle_unpublish_dates(options)
            elif action == 'cleanup':
                return self.handle_cleanup(options)
            else:
                raise CommandError(f"عمل نامعتبر: {action}")
                
        except Exception as e:
            raise CommandError(f"خطا در اجرای دستور: {str(e)}")

    def handle_create_days(self, options):
        """ایجاد روزهای حضور برای یک روز مشخص از هفته"""
        from doctors.turn_maker import create_availability_days_and_slots_for_day_of_week
        
        doctor_id = options.get('doctor_id')
        day_of_week = options.get('day_of_week')
        dry_run = options['dry_run']
        
        if doctor_id is not None and day_of_week is not None:
            raise CommandError("نمی‌توان هم‌زمان --doctor-id و --day-of-week را مشخص کرد. از action generate-doctor-slots استفاده کنید.")
        
        doctors = self.get_doctors(doctor_id)
        total_stats = {
            'days_created': 0,
            'days_updated': 0,
            'days_skipped_holiday': 0,
            'reservations_created': 0,
            'reservations_updated': 0,
        }
        
        for doctor in doctors:
            if not doctor.is_available:
                self.stdout.write(
                    self.style.WARNING(f"رد شد: دکتر {doctor} غیرفعال است")
                )
                continue
            
            doctor_availabilities = doctor.availabilities.all()
            if day_of_week is not None:
                doctor_availabilities = doctor_availabilities.filter(day_of_week=day_of_week)
            
            if not doctor_availabilities.exists():
                self.stdout.write(
                    self.style.WARNING(f"رد شد: دکتر {doctor} زمان‌بندی ندارد")
                )
                continue
            
            if dry_run:
                self.stdout.write(f"[DRY RUN] پردازش دکتر {doctor}")
                for avail in doctor_availabilities:
                    self.stdout.write(f"  - {avail.get_day_of_week_display()}: {avail.start_time} - {avail.end_time}")
                continue
            
            for availability in doctor_availabilities:
                self.stdout.write(f"پردازش دکتر {doctor} - {availability.get_day_of_week_display()}")
                
                stats = create_availability_days_and_slots_for_day_of_week(
                    doctor=doctor,
                    day_of_week=availability.day_of_week,
                    start_time=availability.start_time,
                    end_time=availability.end_time
                )
                
                # جمع آوری آمار
                for key in total_stats:
                    total_stats[key] += stats.get(key, 0)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ {stats['days_created']} روز ایجاد، "
                        f"{stats['reservations_created']} نوبت ایجاد شد"
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nخلاصه کلی:\n"
                f"- روزهای ایجاد شده: {total_stats['days_created']}\n"
                f"- روزهای بروزرسانی شده: {total_stats['days_updated']}\n"
                f"- روزهای تعطیل رد شده: {total_stats['days_skipped_holiday']}\n"
                f"- نوبت‌های ایجاد شده: {total_stats['reservations_created']}\n"
                f"- نوبت‌های بروزرسانی شده: {total_stats['reservations_updated']}"
            )
        )

    def handle_generate_doctor_slots(self, options):
        """تولید نوبت‌ها برای یک پزشک مشخص"""
        from doctors.turn_maker import regenerate_doctor_reservations
        
        doctor_id = options.get('doctor_id')
        dry_run = options['dry_run']
        
        if doctor_id is None:
            raise CommandError("برای این عمل باید --doctor-id مشخص شود")
        
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            raise CommandError(f"پزشک با شناسه {doctor_id} یافت نشد")
        
        if not doctor.is_available:
            raise CommandError(f"دکتر {doctor} غیرفعال است")
        
        if not doctor.availabilities.exists():
            raise CommandError(f"دکتر {doctor} زمان‌بندی ندارد")
        
        if dry_run:
            self.stdout.write(f"[DRY RUN] بازتولید نوبت‌ها برای دکتر {doctor}")
            for avail in doctor.availabilities.all():
                self.stdout.write(f"  - {avail.get_day_of_week_display()}: {avail.start_time} - {avail.end_time}")
            return
        
        self.stdout.write(f"بازتولید نوبت‌ها برای دکتر {doctor}...")
        
        stats = regenerate_doctor_reservations(doctor)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ تکمیل شد:\n"
                f"- زمان‌بندی‌های پردازش شده: {stats['availabilities_processed']}\n"
                f"- روزهای ایجاد شده: {stats['days_created']}\n"
                f"- روزهای بروزرسانی شده: {stats['days_updated']}\n"
                f"- نوبت‌های ایجاد شده: {stats['reservations_created']}\n"
                f"- نوبت‌های بروزرسانی شده: {stats['reservations_updated']}"
            )
        )

    def handle_create_range(self, options):
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
            
            current_date += timedelta(days=1)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'مجموع: {days_created} روز ایجاد شد، {days_skipped} روز رد شد'
            )
        )

    def handle_publish_range(self, options):
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
        
        days.update(published=True)
        self.stdout.write(
            self.style.SUCCESS(f'{count} روز منتشر شد')
        )

    def handle_unpublish_dates(self, options):
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
        
        days.update(published=False)
        self.stdout.write(
            self.style.SUCCESS(f'{count} روز لغو انتشار شد')
        )

    def handle_cleanup(self, options):
        """پاک‌سازی روزهای قدیمی"""
        cutoff_date = timezone.now().date() - timedelta(days=30)
        
        old_days = ReservationDay.objects.filter(
            date__lt=cutoff_date,
            published=False
        )
        
        count = old_days.count()
        
        old_days.delete()
        self.stdout.write(
            self.style.SUCCESS(f'{count} روز قدیمی پاک شد')
        ) 