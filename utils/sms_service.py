from __future__ import absolute_import

import json
import logging
from typing import Optional, Dict, Any

from django.conf import settings
from sms_ir import SmsIr

# Set up logging
logger = logging.getLogger(__name__)

class SMSService:
    """
    SMS service class for sending appointment reminders and notifications
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'SMS_API_KEY', '')
        self.line_number = getattr(settings, 'SMS_LINE_NUMBER', '')
        self.enabled = getattr(settings, 'SMS_REMINDER_ENABLED', False)
        
        if self.enabled and (not self.api_key or not self.line_number):
            logger.error("SMS service is enabled but API_KEY or LINE_NUMBER is missing")
            self.enabled = False
    
    def send_sms(self, number: str, message: str) -> Dict[str, Any]:
        """
        Send SMS to a specific number
        
        Args:
            number (str): Phone number to send SMS to
            message (str): Message content
            
        Returns:
            Dict: Response containing success status and message
        """
        if not self.enabled:
            logger.warning("SMS service is disabled")
            return {
                'success': False,
                'message': 'SMS service is disabled'
            }
        
        if not number or not message:
            logger.error("Phone number or message is empty")
            return {
                'success': False,
                'message': 'Phone number or message cannot be empty'
            }
        
        try:
            # Initialize SMS IR client
            sms_ir = SmsIr(
                api_key=self.api_key,
                linenumber=self.line_number,
            )
            
            # Send SMS
            res = sms_ir.send_sms(
                number=number, 
                message=message, 
                linenumber=self.line_number
            )
            
            logger.info(f"SMS sent successfully to {number}: {res}")
            
            # Extract serializable data from response
            response_data = {
                'status_code': res.status_code,
                'headers': dict(res.headers),
                'url': res.url,
            }
            
            # Try to get JSON content if available
            try:
                response_data['json'] = res.json()
            except:
                response_data['text'] = res.text
            
            return {
                'success': True,
                'message': 'SMS sent successfully',
                'response': response_data
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {number}: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to send SMS: {str(e)}'
            }
    
    def send_appointment_reminder(self, reservation, hours_before: int) -> Dict[str, Any]:
        """
        Send appointment reminder SMS
        
        Args:
            reservation: Reservation object
            hours_before (int): How many hours before the appointment
            
        Returns:
            Dict: Response containing success status and message
        """
        try:
            # Prepare reminder message
            if hours_before == 24:
                message = self._get_24_hour_reminder_message(reservation)
            elif hours_before == 2:
                message = self._get_2_hour_reminder_message(reservation)
            else:
                message = self._get_general_reminder_message(reservation, hours_before)
            
            # Send SMS
            return self.send_sms(reservation.phone, message)
            
        except Exception as e:
            logger.error(f"Failed to send reminder for reservation {reservation.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to send reminder: {str(e)}'
            }
    
    def send_appointment_confirmation(self, reservation) -> Dict[str, Any]:
        """
        Send appointment confirmation SMS
        
        Args:
            reservation: Reservation object
            
        Returns:
            Dict: Response containing success status and message
        """
        try:
            message = self._get_confirmation_message(reservation)
            return self.send_sms(reservation.phone, message)
            
        except Exception as e:
            logger.error(f"Failed to send confirmation for reservation {reservation.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to send confirmation: {str(e)}'
            }
    
    def send_appointment_cancellation(self, reservation) -> Dict[str, Any]:
        """
        Send appointment cancellation SMS
        
        Args:
            reservation: Reservation object
            
        Returns:
            Dict: Response containing success status and message
        """
        try:
            message = self._get_cancellation_message(reservation)
            return self.send_sms(reservation.phone, message)
            
        except Exception as e:
            logger.error(f"Failed to send cancellation for reservation {reservation.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to send cancellation: {str(e)}'
            }
    
    def _get_24_hour_reminder_message(self, reservation) -> str:
        """Generate 24-hour reminder message"""
        patient_name = reservation.patient.name if reservation.patient else "عزیز"
        doctor_name = reservation.doctor.user.get_full_name()
        appointment_date = reservation.day.date.strftime('%Y/%m/%d')
        appointment_time = reservation.time.strftime('%H:%M')
        clinic_name = reservation.doctor.clinic.name if reservation.doctor.clinic else "کلینیک"
        
        message = f"""
سلام {patient_name}
یادآوری نوبت پزشکی:
دکتر: {doctor_name}
تاریخ: {appointment_date}
ساعت: {appointment_time}
مکان: {clinic_name}

برای لغو یا تغییر نوبت با ما تماس بگیرید.
دکتر ترن
        """.strip()
        
        return message
    
    def _get_2_hour_reminder_message(self, reservation) -> str:
        """Generate 2-hour reminder message"""
        patient_name = reservation.patient.name if reservation.patient else "عزیز"
        doctor_name = reservation.doctor.user.get_full_name()
        appointment_time = reservation.time.strftime('%H:%M')
        clinic_address = reservation.doctor.clinic.address if reservation.doctor.clinic else ""
        
        message = f"""
سلام {patient_name}
نوبت شما تا ۲ ساعت دیگر:
دکتر: {doctor_name}
ساعت: {appointment_time}
آدرس: {clinic_address}

لطفاً به موقع حاضر شوید.
دکتر ترن
        """.strip()
        
        return message
    
    def _get_general_reminder_message(self, reservation, hours_before: int) -> str:
        """Generate general reminder message"""
        patient_name = reservation.patient.name if reservation.patient else "عزیز"
        doctor_name = reservation.doctor.user.get_full_name()
        appointment_date = reservation.day.date.strftime('%Y/%m/%d')
        appointment_time = reservation.time.strftime('%H:%M')
        
        message = f"""
سلام {patient_name}
یادآوری نوبت پزشکی:
دکتر: {doctor_name}
تاریخ: {appointment_date}
ساعت: {appointment_time}

{hours_before} ساعت تا نوبت شما باقی مانده.
دکتر ترن
        """.strip()
        
        return message
    
    def _get_confirmation_message(self, reservation) -> str:
        """Generate confirmation message"""
        patient_name = reservation.patient.name if reservation.patient else "عزیز"
        doctor_name = reservation.doctor.user.get_full_name()
        appointment_date = reservation.day.date.strftime('%Y/%m/%d')
        appointment_time = reservation.time.strftime('%H:%M')
        clinic_name = reservation.doctor.clinic.name if reservation.doctor.clinic else "کلینیک"
        
        message = f"""
سلام {patient_name}
نوبت شما تایید شد:
دکتر: {doctor_name}
تاریخ: {appointment_date}
ساعت: {appointment_time}
مکان: {clinic_name}

لطفاً به موقع حاضر شوید.
دکتر ترن
        """.strip()
        
        return message
    
    def _get_cancellation_message(self, reservation) -> str:
        """Generate cancellation message"""
        patient_name = reservation.patient.name if reservation.patient else "عزیز"
        doctor_name = reservation.doctor.user.get_full_name()
        appointment_date = reservation.day.date.strftime('%Y/%m/%d')
        appointment_time = reservation.time.strftime('%H:%M')
        
        message = f"""
سلام {patient_name}
نوبت شما لغو شد:
دکتر: {doctor_name}
تاریخ: {appointment_date}
ساعت: {appointment_time}

در صورت لغو توسط کلینیک، مبلغ به حساب شما بازگردانده می‌شود.
دکتر ترن
        """.strip()
        
        return message


# Create a singleton instance
sms_service = SMSService()


def send_sms(number: str, message: str) -> Dict[str, Any]:
    """
    Convenience function for sending SMS
    This is the function you provided, now properly integrated
    """
    return sms_service.send_sms(number, message)


def send_appointment_reminder(reservation, hours_before: int) -> Dict[str, Any]:
    """Convenience function for sending appointment reminders"""
    return sms_service.send_appointment_reminder(reservation, hours_before)


def send_appointment_confirmation(reservation) -> Dict[str, Any]:
    """Convenience function for sending appointment confirmations"""
    return sms_service.send_appointment_confirmation(reservation)


def send_appointment_cancellation(reservation) -> Dict[str, Any]:
    """Convenience function for sending appointment cancellations"""
    return sms_service.send_appointment_cancellation(reservation) 