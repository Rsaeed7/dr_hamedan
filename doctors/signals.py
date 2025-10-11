"""
سیگنال‌های مربوط به مدیریت خودکار نوبت‌های پزشک
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db import transaction
from .models import DoctorAvailability
from reservations.turn_maker import create_availability_days_and_slots_for_day_of_week, update_doctor_availability_slots
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


# =============================================================================
# Notification Signals
# =============================================================================

@receiver(post_save, sender='reservations.Reservation')
def create_appointment_notifications(sender, instance, created, **kwargs):
    """
    ایجاد اعلان‌های مربوط به نوبت‌ها
    """
    try:
        from .models import Notification
        from datetime import datetime, timedelta
        
        # اعلان برای پزشک در صورت رزرو نوبت جدید
        # این اعلان هم برای نوبت‌های جدید و هم برای بروزرسانی نوبت‌های موجود ارسال می‌شود
        if instance.status in ['pending', 'confirmed'] and instance.patient:
            
            # بررسی اینکه آیا این اعلان قبلاً برای این نوبت ارسال شده یا نه
            existing_notification = Notification.objects.filter(
                user=instance.doctor.user,
                metadata__appointment_id=instance.id,
                notification_type='appointment'
            ).first()
            
            # فقط اگر اعلان قبلی وجود نداشته باشد، اعلان جدید ایجاد کن
            if not existing_notification:
                Notification.create_notification(
                    user=instance.doctor.user,
                    title='نوبت جدید رزرو شد',
                    message=f'بیمار {instance.patient.user.get_full_name()} نوبت جدیدی در تاریخ {instance.day.date} ساعت {instance.time} رزرو کرد.',
                    notification_type='appointment',
                    priority='medium',
                    link=f'/doctors/appointments/',
                    metadata={
                        'appointment_id': instance.id,
                        'patient_name': instance.patient.user.get_full_name(),
                        'appointment_date': str(instance.day.date),
                        'appointment_time': str(instance.time)
                    }
                )
            
        # اعلان یادآوری برای پزشک (یک ساعت قبل از نوبت)
        if instance.status == 'confirmed' and instance.patient:
            try:
                # Use Django timezone-aware datetime
                from django.utils import timezone
                import jdatetime
                
                # Convert Jalali date to Gregorian datetime
                jalali_date = instance.day.date
                if hasattr(jalali_date, 'togregorian'):
                    gregorian_date = jalali_date.togregorian()
                else:
                    gregorian_date = jalali_date
                    
                appointment_datetime = datetime.combine(gregorian_date, instance.time)
                appointment_datetime = timezone.make_aware(appointment_datetime)
                reminder_time = appointment_datetime - timedelta(hours=1)
                
                if reminder_time > timezone.now():
                    Notification.create_notification(
                        user=instance.doctor.user,
                        title='یادآوری نوبت',
                        message=f'نوبت شما با بیمار {instance.patient.user.get_full_name()} یک ساعت دیگر آغاز می‌شود.',
                        notification_type='appointment',
                        priority='high',
                        link=f'/doctors/appointments/',
                        metadata={
                            'appointment_id': instance.id,
                            'patient_name': instance.patient.user.get_full_name(),
                            'appointment_date': str(instance.day.date),
                            'appointment_time': str(instance.time)
                        },
                        expires_at=appointment_datetime + timedelta(hours=1)
                    )
            except Exception as e:
                logger.error(f"Error creating reminder notification: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error creating appointment notifications: {str(e)}")


@receiver(post_save, sender='doctors.DrComment')
def create_comment_notifications(sender, instance, created, **kwargs):
    """
    اعلان‌های مربوط به نظرات پزشک
    """
    if not created:
        return
    
    try:
        from .models import Notification
        
        # اعلان برای پزشک در صورت ثبت نظر جدید
        if instance.status == 'checking':
            Notification.create_notification(
                user=instance.doctor.user,
                title='نظر جدید دریافت شد',
                message=f'یک نظر جدید از بیمار {instance.user.get_full_name() if instance.user else "ناشناس"} برای شما ثبت شد.',
                notification_type='message',
                priority='medium',
                link=f'/doctors/doctor/{instance.doctor.slug}/',
                metadata={
                    'comment_id': instance.id,
                    'patient_name': instance.user.get_full_name() if instance.user else 'ناشناس',
                    'rating': instance.rate
                }
            )
            
        # اعلان در صورت تایید نظر
        elif instance.status == 'confirmed':
            Notification.create_notification(
                user=instance.doctor.user,
                title='نظر شما تایید شد',
                message=f'نظر جدید شما با امتیاز {instance.rate} تایید و منتشر شد.',
                notification_type='success',
                priority='low',
                link=f'/doctors/doctor/{instance.doctor.slug}/',
                metadata={
                    'comment_id': instance.id,
                    'rating': instance.rate
                }
            )
            
    except Exception as e:
        logger.error(f"Error creating comment notifications: {str(e)}")


@receiver(post_save, sender='doctors.Email')
def create_email_notifications(sender, instance, created, **kwargs):
    """
    اعلان‌های مربوط به نامه‌های پزشک
    """
    if not created:
        return
    
    try:
        from .models import Notification
        
        # اعلان برای گیرنده نامه
        Notification.create_notification(
            user=instance.recipient.user,
            title='نامه جدید دریافت شد',
            message=f'نامه جدیدی از دکتر {instance.sender.user.get_full_name()} با موضوع "{instance.subject}" دریافت کردید.',
            notification_type='message',
            priority='medium',
            link=f'/doctors/message/{instance.slug}/',
            metadata={
                'email_id': str(instance.id),
                'sender_name': instance.sender.user.get_full_name(),
                'subject': instance.subject
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating email notifications: {str(e)}")


@receiver(post_save, sender='doctors.DoctorRegistration')
def create_registration_notifications(sender, instance, created, **kwargs):
    """
    اعلان‌های مربوط به ثبت‌نام پزشک
    """
    if created:
        try:
            from .models import Notification
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # اعلان برای ادمین‌ها
            admin_users = User.objects.filter(is_staff=True, is_active=True)
            for admin in admin_users:
                Notification.create_notification(
                    user=admin,
                    title='درخواست عضویت پزشک جدید',
                    message=f'درخواست عضویت جدیدی از دکتر {instance.first_name} {instance.last_name} دریافت شد.',
                    notification_type='system',
                    priority='high',
                    link=f'/admin/doctors/doctorregistration/{instance.id}/change/',
                    metadata={
                        'registration_id': instance.id,
                        'doctor_name': f'{instance.first_name} {instance.last_name}',
                        'specialization': instance.specialization.name if instance.specialization else 'نامشخص'
                    }
                )
                
        except Exception as e:
            logger.error(f"Error creating registration notifications: {str(e)}")
    
    # اعلان در صورت تغییر وضعیت
    elif hasattr(instance, '_state') and instance._state.db:
        try:
            from .models import Notification
            
            # بررسی تغییر وضعیت
            if instance.status == 'approved':
                # اعلان تایید به متقاضی (اگر کاربر ایجاد شده باشد)
                if hasattr(instance, 'user') and instance.user:
                    Notification.create_notification(
                        user=instance.user,
                        title='درخواست شما تایید شد',
                        message='درخواست عضویت شما به عنوان پزشک تایید شد. اکنون می‌توانید از سیستم استفاده کنید.',
                        notification_type='success',
                        priority='high',
                        link='/doctors/dashboard/',
                        metadata={
                            'registration_id': instance.id
                        }
                    )
                    
            elif instance.status == 'rejected':
                # اعلان رد به متقاضی
                if hasattr(instance, 'user') and instance.user:
                    Notification.create_notification(
                        user=instance.user,
                        title='درخواست شما رد شد',
                        message=f'درخواست عضویت شما رد شد. دلیل: {instance.admin_notes or "دلیل خاصی ذکر نشده است."}',
                        notification_type='error',
                        priority='high',
                        metadata={
                            'registration_id': instance.id,
                            'reason': instance.admin_notes or ''
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Error creating registration status notifications: {str(e)}")


@receiver(post_save, sender='wallet.Transaction')
def create_transaction_notifications(sender, instance, created, **kwargs):
    """
    اعلان‌های مربوط به تراکنش‌های مالی
    """
    if not created:
        return
    
    try:
        from .models import Notification
        
        # اعلان برای پزشک در صورت دریافت پرداخت
        if instance.transaction_type == 'payment' and instance.status == 'completed':
            if hasattr(instance.user, 'doctor'):
                Notification.create_notification(
                    user=instance.user,
                    title='درآمد جدید',
                    message=f'مبلغ {instance.amount:,} تومان از نوبت شما به حساب شما واریز شد.',
                    notification_type='success',
                    priority='medium',
                    link='/doctors/earnings/',
                    metadata={
                        'transaction_id': instance.id,
                        'amount': float(instance.amount)
                    }
                )
                
        # اعلان برای واریز به کیف پول
        elif instance.transaction_type == 'deposit' and instance.status == 'completed':
            Notification.create_notification(
                user=instance.user,
                title='واریز موفق',
                message=f'مبلغ {instance.amount:,} تومان با موفقیت به کیف پول شما واریز شد.',
                notification_type='success',
                priority='low',
                link='/wallet/dashboard/',
                metadata={
                    'transaction_id': instance.id,
                    'amount': float(instance.amount)
                }
            )
            
    except Exception as e:
        logger.error(f"Error creating transaction notifications: {str(e)}")


@receiver(post_save, sender='doctors.DoctorBlockedDay')
def create_blocked_day_notifications(sender, instance, created, **kwargs):
    """
    اعلان‌های مربوط به روزهای مسدود شده پزشک
    """
    if not created:
        return
    
    try:
        from .models import Notification
        
        # اعلان برای پزشک
        Notification.create_notification(
            user=instance.doctor.user,
            title='روز مسدود شده ثبت شد',
            message=f'تاریخ {instance.date} با موفقیت مسدود شد. {instance.reason if instance.reason else ""}',
            notification_type='info',
            priority='low',
            link='/doctors/blocked-days/',
            metadata={
                'blocked_day_id': instance.id,
                'date': str(instance.date),
                'reason': instance.reason or ''
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating blocked day notifications: {str(e)}")


# سیگنال برای پاکسازی اعلان‌های منقضی شده
from django.core.management import call_command
from django.db.models.signals import post_migrate

@receiver(post_migrate)
def setup_notification_cleanup(sender, **kwargs):
    """
    راه‌اندازی پاکسازی خودکار اعلان‌های منقضی شده
    """
    if sender.name == 'doctors':
        try:
            from .models import Notification
            # پاکسازی اعلان‌های منقضی شده
            Notification.cleanup_expired()
            logger.info("Expired notifications cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up expired notifications: {str(e)}") 