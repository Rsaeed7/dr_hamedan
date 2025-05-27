"""
سیگنال‌های مربوط به مدیریت خودکار نوبت‌های پزشک
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db import transaction
from .models import DoctorAvailability
from .turn_maker import (
    create_availability_days_and_slots_for_day_of_week,
    update_doctor_availability_slots,
    regenerate_doctor_reservations
)
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=DoctorAvailability)
def handle_availability_created_or_updated(sender, instance, created, **kwargs):
    """
    مدیریت ایجاد یا بروزرسانی زمان‌بندی پزشک
    """
    try:
        if created:
            # ایجاد نوبت‌های جدید برای این زمان‌بندی
            logger.info(f"Creating new availability slots for Dr. {instance.doctor} on {instance.get_day_of_week_display()}")
            
            with transaction.atomic():
                stats = create_availability_days_and_slots_for_day_of_week(
                    doctor=instance.doctor,
                    day_of_week=instance.day_of_week,
                    start_time=instance.start_time,
                    end_time=instance.end_time
                )
                
                logger.info(f"Created {stats['reservations_created']} new reservation slots")
                
        else:
            # بروزرسانی نوبت‌های موجود
            logger.info(f"Updating availability slots for Dr. {instance.doctor} on {instance.get_day_of_week_display()}")
            
            # برای بروزرسانی، باید زمان‌های قبلی را بدانیم
            # این کار پیچیده است، پس بازتولید کامل می‌کنیم
            with transaction.atomic():
                # ابتدا نوبت‌های آزاد قدیمی را حذف کنیم
                from reservations.models import Reservation, ReservationDay
                from datetime import datetime, timedelta
                
                today = datetime.now().date()
                future_date = today + timedelta(days=365)
                
                # حذف نوبت‌های آزاد برای این روز از هفته
                deleted_count = 0
                current_date = today
                while current_date <= future_date:
                    gregorian_day_of_week = current_date.weekday()
                    persian_day_of_week = (gregorian_day_of_week + 2) % 7
                    
                    if persian_day_of_week == instance.day_of_week:
                        try:
                            reservation_day = ReservationDay.objects.get(date=current_date, published=True)
                            deleted = Reservation.objects.filter(
                                day=reservation_day,
                                doctor=instance.doctor,
                                status='available'
                            ).delete()
                            deleted_count += deleted[0]
                        except ReservationDay.DoesNotExist:
                            pass
                    
                    current_date += timedelta(days=1)
                
                logger.info(f"Deleted {deleted_count} old available slots")
                
                # ایجاد نوبت‌های جدید
                stats = create_availability_days_and_slots_for_day_of_week(
                    doctor=instance.doctor,
                    day_of_week=instance.day_of_week,
                    start_time=instance.start_time,
                    end_time=instance.end_time
                )
                
                logger.info(f"Created {stats['reservations_created']} new reservation slots")
                
    except Exception as e:
        logger.error(f"Error handling availability change: {str(e)}")


@receiver(post_delete, sender=DoctorAvailability)
def handle_availability_deleted(sender, instance, **kwargs):
    """
    مدیریت حذف زمان‌بندی پزشک
    """
    try:
        logger.info(f"Deleting availability slots for Dr. {instance.doctor} on {instance.get_day_of_week_display()}")
        
        with transaction.atomic():
            from reservations.models import Reservation, ReservationDay
            from datetime import datetime, timedelta
            
            today = datetime.now().date()
            future_date = today + timedelta(days=365)
            
            # حذف تمام نوبت‌های آزاد برای این روز از هفته
            deleted_count = 0
            current_date = today
            while current_date <= future_date:
                gregorian_day_of_week = current_date.weekday()
                persian_day_of_week = (gregorian_day_of_week + 2) % 7
                
                if persian_day_of_week == instance.day_of_week:
                    try:
                        reservation_day = ReservationDay.objects.get(date=current_date, published=True)
                        deleted = Reservation.objects.filter(
                            day=reservation_day,
                            doctor=instance.doctor,
                            status='available'
                        ).delete()
                        deleted_count += deleted[0]
                    except ReservationDay.DoesNotExist:
                        pass
                
                current_date += timedelta(days=1)
            
            logger.info(f"Deleted {deleted_count} available slots")
            
    except Exception as e:
        logger.error(f"Error handling availability deletion: {str(e)}")


# ذخیره داده‌های قبلی برای مقایسه در هنگام بروزرسانی
_availability_old_values = {}

@receiver(pre_save, sender=DoctorAvailability)
def store_old_availability_values(sender, instance, **kwargs):
    """
    ذخیره مقادیر قبلی برای مقایسه در زمان بروزرسانی
    """
    if instance.pk:
        try:
            old_instance = DoctorAvailability.objects.get(pk=instance.pk)
            _availability_old_values[instance.pk] = {
                'start_time': old_instance.start_time,
                'end_time': old_instance.end_time,
                'day_of_week': old_instance.day_of_week
            }
        except DoctorAvailability.DoesNotExist:
            pass 