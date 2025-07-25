import logging
from datetime import datetime, timedelta, time
from typing import List, Optional, Dict, Any
from django.utils import timezone
from django.conf import settings
from django.db import transaction
import json

from .models import SMSReminder, SMSReminderTemplate, SMSReminderSettings, SMSLog
from reservations.models import Reservation
from utils.sms_service import sms_service

logger = logging.getLogger(__name__)


class SMSReminderService:
    """
    Service class for managing SMS reminders
    """
    
    def __init__(self):
        self.settings = SMSReminderSettings.get_settings()
    
    def schedule_appointment_reminders(self, reservation: Reservation) -> List[SMSReminder]:
        """
        Schedule all necessary reminders for an appointment
        
        Args:
            reservation: The reservation to schedule reminders for
            
        Returns:
            List of created SMS reminder objects
        """
        reminders = []
        
        try:
            # Get appointment datetime
            appointment_datetime = self._get_appointment_datetime(reservation)
            
            # Schedule 24-hour reminder
            if self.settings.reminder_24h_enabled:
                reminder_24h = self._schedule_reminder(
                    reservation=reservation,
                    reminder_type='reminder_24h',
                    hours_before=24,
                    appointment_datetime=appointment_datetime
                )
                if reminder_24h:
                    reminders.append(reminder_24h)
            
            # Schedule 2-hour reminder
            if self.settings.reminder_2h_enabled:
                reminder_2h = self._schedule_reminder(
                    reservation=reservation,
                    reminder_type='reminder_2h',
                    hours_before=2,
                    appointment_datetime=appointment_datetime
                )
                if reminder_2h:
                    reminders.append(reminder_2h)
            
            logger.info(f"Scheduled {len(reminders)} reminders for reservation {reservation.id}")
            
        except Exception as e:
            logger.error(f"Failed to schedule reminders for reservation {reservation.id}: {str(e)}")
        
        return reminders
    
    def send_confirmation_sms(self, reservation: Reservation) -> Optional[SMSReminder]:
        """
        Send immediate confirmation SMS for an appointment
        
        Args:
            reservation: The reservation to send confirmation for
            
        Returns:
            SMS reminder object if created and sent successfully
        """
        if not self.settings.confirmation_sms_enabled:
            logger.info("Confirmation SMS is disabled")
            return None
        
        try:
            # Get phone number from patient
            phone_number = reservation.patient.phone if reservation.patient else None
            if not phone_number:
                logger.error(f"No phone number found for reservation {reservation.id}")
                return None
            
            # Create confirmation reminder
            reminder = SMSReminder.objects.create(
                reservation=reservation,
                user=reservation.patient.user if reservation.patient else reservation.user,
                reminder_type='confirmation',
                phone_number=phone_number,
                message=self._generate_message(reservation, 'confirmation'),
                scheduled_time=timezone.now(),
                max_attempts=self.settings.max_retry_attempts
            )
            
            # Send immediately
            self._send_reminder(reminder)
            
            logger.info(f"Sent confirmation SMS for reservation {reservation.id}")
            return reminder
            
        except Exception as e:
            logger.error(f"Failed to send confirmation SMS for reservation {reservation.id}: {str(e)}")
            return None
    
    def send_cancellation_sms(self, reservation: Reservation) -> Optional[SMSReminder]:
        """
        Send cancellation SMS for an appointment
        
        Args:
            reservation: The reservation that was cancelled
            
        Returns:
            SMS reminder object if created and sent successfully
        """
        if not self.settings.cancellation_sms_enabled:
            logger.info("Cancellation SMS is disabled")
            return None
        
        try:
            # Get phone number from patient
            phone_number = reservation.patient.phone if reservation.patient else None
            if not phone_number:
                logger.error(f"No phone number found for reservation {reservation.id}")
                return None
            
            # Create cancellation reminder
            reminder = SMSReminder.objects.create(
                reservation=reservation,
                user=reservation.patient.user if reservation.patient else reservation.user,
                reminder_type='cancellation',
                phone_number=phone_number,
                message=self._generate_message(reservation, 'cancellation'),
                scheduled_time=timezone.now(),
                max_attempts=self.settings.max_retry_attempts
            )
            
            # Send immediately
            self._send_reminder(reminder)
            
            logger.info(f"Sent cancellation SMS for reservation {reservation.id}")
            return reminder
            
        except Exception as e:
            logger.error(f"Failed to send cancellation SMS for reservation {reservation.id}: {str(e)}")
            return None
    
    def process_pending_reminders(self) -> Dict[str, int]:
        """
        Process all pending reminders that are due to be sent
        
        Returns:
            Dictionary with counts of processed reminders
        """
        stats = {
            'sent': 0,
            'failed': 0,
            'skipped': 0
        }
        
        try:
            # Get reminders that are due to be sent
            now = timezone.now()
            pending_reminders = SMSReminder.objects.filter(
                status='pending',
                scheduled_time__lte=now
            ).select_related('reservation', 'user')
            
            logger.info(f"Processing {pending_reminders.count()} pending reminders")
            
            for reminder in pending_reminders:
                # Check if reminder should be sent during working hours
                if not self._is_within_working_hours(reminder.scheduled_time):
                    # Reschedule to next working hour
                    reminder.scheduled_time = self._get_next_working_hour()
                    reminder.save()
                    stats['skipped'] += 1
                    continue
                
                # Send the reminder
                if self._send_reminder(reminder):
                    stats['sent'] += 1
                else:
                    stats['failed'] += 1
            
            logger.info(f"Processed reminders - Sent: {stats['sent']}, Failed: {stats['failed']}, Skipped: {stats['skipped']}")
            
        except Exception as e:
            logger.error(f"Error processing pending reminders: {str(e)}")
        
        return stats
    
    def retry_failed_reminders(self) -> Dict[str, int]:
        """
        Retry failed reminders that can still be retried
        
        Returns:
            Dictionary with counts of retried reminders
        """
        stats = {
            'retried': 0,
            'sent': 0,
            'failed': 0
        }
        
        try:
            # Get failed reminders that can be retried
            failed_reminders = SMSReminder.objects.filter(
                status='failed'
            ).select_related('reservation', 'user')
            
            for reminder in failed_reminders:
                if reminder.can_retry():
                    # Check if enough time has passed since last attempt
                    if self._can_retry_now(reminder):
                        reminder.retry()
                        stats['retried'] += 1
                        
                        # Try to send again
                        if self._send_reminder(reminder):
                            stats['sent'] += 1
                        else:
                            stats['failed'] += 1
            
            logger.info(f"Retry process - Retried: {stats['retried']}, Sent: {stats['sent']}, Failed: {stats['failed']}")
            
        except Exception as e:
            logger.error(f"Error retrying failed reminders: {str(e)}")
        
        return stats
    
    def cancel_reminders_for_reservation(self, reservation: Reservation) -> int:
        """
        Cancel all pending reminders for a reservation
        
        Args:
            reservation: The reservation to cancel reminders for
            
        Returns:
            Number of cancelled reminders
        """
        try:
            cancelled_count = SMSReminder.objects.filter(
                reservation=reservation,
                status='pending'
            ).update(status='cancelled')
            
            logger.info(f"Cancelled {cancelled_count} reminders for reservation {reservation.id}")
            return cancelled_count
            
        except Exception as e:
            logger.error(f"Failed to cancel reminders for reservation {reservation.id}: {str(e)}")
            return 0
    
    def _schedule_reminder(self, reservation: Reservation, reminder_type: str, 
                          hours_before: int, appointment_datetime: datetime) -> Optional[SMSReminder]:
        """
        Schedule a single reminder
        """
        try:
            # Calculate when to send the reminder
            scheduled_time = appointment_datetime - timedelta(hours=hours_before)
            
            # Don't schedule if the time has already passed
            if scheduled_time <= timezone.now():
                logger.warning(f"Cannot schedule {reminder_type} for reservation {reservation.id} - time has passed")
                return None
            
            # Check if reminder already exists
            existing = SMSReminder.objects.filter(
                reservation=reservation,
                reminder_type=reminder_type
            ).first()
            
            if existing:
                logger.info(f"Reminder {reminder_type} already exists for reservation {reservation.id}")
                return existing
            
            # Get phone number from patient
            phone_number = reservation.patient.phone if reservation.patient else None
            if not phone_number:
                logger.error(f"No phone number found for reservation {reservation.id}")
                return None
            
            # Create the reminder
            reminder = SMSReminder.objects.create(
                reservation=reservation,
                user=reservation.patient.user if reservation.patient else reservation.user,
                reminder_type=reminder_type,
                phone_number=phone_number,
                message=self._generate_message(reservation, reminder_type),
                scheduled_time=scheduled_time,
                max_attempts=self.settings.max_retry_attempts
            )
            
            logger.info(f"Scheduled {reminder_type} for reservation {reservation.id} at {scheduled_time}")
            return reminder
            
        except Exception as e:
            logger.error(f"Failed to schedule {reminder_type} for reservation {reservation.id}: {str(e)}")
            return None
    
    def _send_reminder(self, reminder: SMSReminder) -> bool:
        """
        Send a single reminder
        """
        try:
            # Send the SMS
            result = sms_service.send_sms(reminder.phone_number, reminder.message)
            
            # Prepare response data for storage (handle non-serializable objects)
            response_data = result.get('response')
            if response_data:
                try:
                    # Test if response_data is JSON serializable
                    json.dumps(response_data)
                except (TypeError, ValueError):
                    # Convert non-serializable objects to string
                    response_data = str(response_data)
            
            # Log the attempt
            SMSLog.objects.create(
                phone_number=reminder.phone_number,
                message=reminder.message,
                reminder=reminder,
                success=result['success'],
                response_data=response_data,
                error_message=result.get('message') if not result['success'] else None
            )
            
            if result['success']:
                reminder.mark_as_sent(response_data)
                logger.info(f"Successfully sent reminder {reminder.id}")
                return True
            else:
                reminder.mark_as_failed(result['message'])
                logger.error(f"Failed to send reminder {reminder.id}: {result['message']}")
                return False
                
        except Exception as e:
            error_message = f"Exception sending reminder: {str(e)}"
            reminder.mark_as_failed(error_message)
            logger.error(f"Exception sending reminder {reminder.id}: {str(e)}")
            return False
    
    def _generate_message(self, reservation: Reservation, reminder_type: str) -> str:
        """
        Generate message content for a reminder
        """
        try:
            # Try to get custom template first
            template = SMSReminderTemplate.objects.filter(
                reminder_type=reminder_type,
                is_active=True
            ).first()
            
            if template:
                return template.render_message(reservation)
            
            # Fallback to built-in messages
            if reminder_type == 'confirmation':
                return sms_service._get_confirmation_message(reservation)
            elif reminder_type == 'reminder_24h':
                return sms_service._get_24_hour_reminder_message(reservation)
            elif reminder_type == 'reminder_2h':
                return sms_service._get_2_hour_reminder_message(reservation)
            elif reminder_type == 'cancellation':
                return sms_service._get_cancellation_message(reservation)
            else:
                return sms_service._get_general_reminder_message(reservation, 1)
                
        except Exception as e:
            logger.error(f"Failed to generate message for {reminder_type}: {str(e)}")
            return "پیام یادآوری نوبت پزشکی - دکتر ترن"
    
    def _get_appointment_datetime(self, reservation: Reservation) -> datetime:
        """
        Get full datetime for an appointment
        """
        appointment_date = reservation.day.date
        appointment_time = reservation.time
        
        # Convert Jalali date to standard Python date if needed
        if hasattr(appointment_date, 'togregorian'):
            appointment_date = appointment_date.togregorian()
        
        # Combine date and time
        appointment_datetime = datetime.combine(appointment_date, appointment_time)
        
        # Make timezone aware
        if timezone.is_naive(appointment_datetime):
            appointment_datetime = timezone.make_aware(appointment_datetime)
        
        return appointment_datetime
    
    def _is_within_working_hours(self, dt: datetime) -> bool:
        """
        Check if a datetime is within working hours
        """
        time_only = dt.time()
        
        # Ensure working hours are time objects
        start_time = self.settings.working_hour_start
        end_time = self.settings.working_hour_end
        
        # Convert string to time if needed
        if isinstance(start_time, str):
            hour, minute = map(int, start_time.split(':'))
            start_time = time(hour, minute)
        
        if isinstance(end_time, str):
            hour, minute = map(int, end_time.split(':'))
            end_time = time(hour, minute)
        
        return start_time <= time_only <= end_time
    
    def _get_next_working_hour(self) -> datetime:
        """
        Get the next working hour
        """
        now = timezone.now()
        
        # If currently within working hours, return current time
        if self._is_within_working_hours(now):
            return now
        
        # Get start time as time object
        start_time = self.settings.working_hour_start
        if isinstance(start_time, str):
            hour, minute = map(int, start_time.split(':'))
            start_time = time(hour, minute)
        
        # Otherwise, schedule for tomorrow at start of working hours
        next_day = now.replace(hour=start_time.hour,
                              minute=start_time.minute,
                              second=0,
                              microsecond=0) + timedelta(days=1)
        
        return next_day
    
    def _can_retry_now(self, reminder: SMSReminder) -> bool:
        """
        Check if enough time has passed to retry a failed reminder
        """
        if not reminder.updated_at:
            return True
        
        time_since_last_attempt = timezone.now() - reminder.updated_at
        retry_interval = timedelta(minutes=self.settings.retry_interval_minutes)
        
        return time_since_last_attempt >= retry_interval


# Create a singleton instance
sms_reminder_service = SMSReminderService()


# Convenience functions
def schedule_appointment_reminders(reservation: Reservation) -> List[SMSReminder]:
    """Schedule reminders for an appointment"""
    return sms_reminder_service.schedule_appointment_reminders(reservation)


def send_confirmation_sms(reservation: Reservation) -> Optional[SMSReminder]:
    """Send confirmation SMS for an appointment"""
    return sms_reminder_service.send_confirmation_sms(reservation)


def send_cancellation_sms(reservation: Reservation) -> Optional[SMSReminder]:
    """Send cancellation SMS for an appointment"""
    return sms_reminder_service.send_cancellation_sms(reservation)


def process_pending_reminders() -> Dict[str, int]:
    """Process all pending reminders"""
    return sms_reminder_service.process_pending_reminders()


def retry_failed_reminders() -> Dict[str, int]:
    """Retry failed reminders"""
    return sms_reminder_service.retry_failed_reminders()


def cancel_reminders_for_reservation(reservation: Reservation) -> int:
    """Cancel reminders for a reservation"""
    return sms_reminder_service.cancel_reminders_for_reservation(reservation) 