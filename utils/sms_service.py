from __future__ import absolute_import

import json
import logging
import random
import threading
import time
from typing import Optional, Dict, Any
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from sms_ir import SmsIr

# Set up logging
logger = logging.getLogger(__name__)


class SMSService:
    """
    Centralized SMS service class for all SMS functionality using SmsIr API
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'SMS_API_KEY', '')
        self.line_number = getattr(settings, 'SMS_LINE_NUMBER', '')
        self.enabled = getattr(settings, 'SMS_REMINDER_ENABLED', True)
        
        # Template IDs for different SMS types
        self.otp_template_id = getattr(settings, 'SMS_OTP_TEMPLATE_ID', 100000)
        
        if self.enabled and (not self.api_key or not self.line_number):
            logger.error("SMS service is enabled but API_KEY or LINE_NUMBER is missing")
            self.enabled = False
    
    def send_sms(self, number: str, message: str) -> Dict[str, Any]:
        """
        Send regular SMS to a specific number using SmsIr bulk API
        
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
            
            # Send SMS using the bulk method for regular messages
            res = sms_ir.send_bulk_sms(
                numbers=[number], 
                message=message, 
                linenumber=self.line_number
            )
            
            logger.info(f"SMS sent successfully to {number}")
            
            # Extract response data
            response_data = {
                'status_code': res.status_code if hasattr(res, 'status_code') else 200,
                'success': res.status_code == 200 if hasattr(res, 'status_code') else True
            }
            
            # Try to get JSON content if available
            try:
                if hasattr(res, 'json'):
                    response_data['json'] = res.json()
                elif hasattr(res, 'text'):
                    response_data['text'] = res.text
            except:
                pass
            
            return {
                'success': response_data.get('success', True),
                'message': 'SMS sent successfully',
                'response': response_data
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {number}: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to send SMS: {str(e)}'
            }
    
    def send_verification_code(self, phone_number: str, template_id: int = None) -> tuple:
        """
        Send verification code using SmsIr verify API
        
        Args:
            phone_number (str): Phone number to send OTP to
            template_id (int): Template ID for OTP (optional)
            
        Returns:
            tuple: (message, status_code, otp_code)
        """
        if not self.enabled:
            return ("سرویس پیامک غیرفعال است", 503, None)
        
        try:
            # Generate OTP code
            code = str(random.randrange(1000, 9999))
            code = code.replace("0", "5")  # Replace 0 with 5 to avoid confusion
            
            # Use provided template or default
            template = template_id or self.otp_template_id
            
            # Convert phone number to integer format (remove leading zero)
            # e.g., "09123456789" becomes 9123456789
            if phone_number.startswith('0'):
                phone_number_int = int(phone_number[1:])
            else:
                phone_number_int = int(phone_number)
            
            # Initialize SMS IR client
            sms_ir = SmsIr(
                api_key=self.api_key,
                linenumber=self.line_number,
            )
            
            # Send verification SMS using the correct method name
            parameters = [{"name": "Code", "value": code}]
            
            logger.info(f"Sending verification code to {phone_number} with template {template}")
            
            res = sms_ir.send_verify_code(
                number=phone_number_int,
                template_id=template,
                parameters=parameters
            )
            
            # Check response based on SMS.ir response format
            if res and hasattr(res, 'status_code') and res.status_code == 200:
                # Try to get JSON response for better error handling
                try:
                    json_response = res.json()
                    if json_response.get('status') == 1:  # SMS.ir success status
                        logger.info(f"Verification code sent successfully to {phone_number}")
                        return ("کد تایید برای شما ارسال شد", 200, code)
                    else:
                        error_msg = json_response.get('message', 'خطا در ارسال')
                        logger.error(f"SMS.ir error: {error_msg}")
                        return (error_msg, 400, None)
                except:
                    # If JSON parsing fails but status is 200, assume success
                    logger.info(f"Verification code sent successfully to {phone_number} (no JSON)")
                    return ("کد تایید برای شما ارسال شد", 200, code)
            else:
                logger.error(f"Failed to send verification code: status={getattr(res, 'status_code', 'unknown')}")
                return ("خطا در ارسال کد تایید", 500, None)
                
        except AttributeError as e:
            # This specific error suggests the method name issue
            logger.error(f"AttributeError in send_verification_code: {str(e)}")
            if "send_verify" in str(e):
                return ("خطا در پیکربندی سرویس پیامک", 500, None)
            return (f"خطا در ارسال پیامک: {str(e)}", 500, None)
        except Exception as e:
            logger.error(f"Exception sending verification code to {phone_number}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            return (f"خطا در ارسال پیامک: {str(e)}", 500, None)
    
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
            # Get phone number from patient
            phone_number = reservation.patient.phone if reservation.patient else None
            if not phone_number:
                return {
                    'success': False,
                    'message': 'Patient phone number not found'
                }
            
            # Prepare reminder message
            if hours_before == 24:
                message = self._get_24_hour_reminder_message(reservation)
            elif hours_before == 2:
                message = self._get_2_hour_reminder_message(reservation)
            else:
                message = self._get_general_reminder_message(reservation, hours_before)
            
            # Send SMS
            return self.send_sms(phone_number, message)
            
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
            # Get phone number from patient
            phone_number = reservation.patient.phone if reservation.patient else None
            if not phone_number:
                return {
                    'success': False,
                    'message': 'Patient phone number not found'
                }
            
            message = self._get_confirmation_message(reservation)
            return self.send_sms(phone_number, message)
            
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
            # Get phone number from patient
            phone_number = reservation.patient.phone if reservation.patient else None
            if not phone_number:
                return {
                    'success': False,
                    'message': 'Patient phone number not found'
                }
            
            message = self._get_cancellation_message(reservation)
            return self.send_sms(phone_number, message)
            
        except Exception as e:
            logger.error(f"Failed to send cancellation for reservation {reservation.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to send cancellation: {str(e)}'
            }
    
    def send_doctor_approval(self, doctor_user, username: str, password: str) -> Dict[str, Any]:
        """
        Send doctor approval notification with credentials
        
        Args:
            doctor_user: User object for the doctor
            username (str): Generated username
            password (str): Generated password
            
        Returns:
            Dict: Response containing success status and message
        """
        try:
            message = f"""درخواست عضویت شما به عنوان پزشک تایید شد.
نام کاربری: {username}
رمز عبور موقت: {password}
لطفاً پس از ورود، رمز عبور خود را تغییر دهید.
دکتر ترن"""
            
            return self.send_sms(doctor_user.phone, message)
            
        except Exception as e:
            logger.error(f"Failed to send doctor approval to {doctor_user.phone}: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to send approval: {str(e)}'
            }
    
    def _get_24_hour_reminder_message(self, reservation) -> str:
        """Generate 24-hour reminder message"""
        patient_name = reservation.patient.name if reservation.patient else "عزیز"
        doctor_name = reservation.doctor.user.get_full_name()
        appointment_date = reservation.day.date.strftime('%Y/%m/%d')
        appointment_time = reservation.time.strftime('%H:%M')
        clinic_name = reservation.doctor.clinic.name if reservation.doctor.clinic else "کلینیک"
        
        message = f"""سلام {patient_name}
یادآوری نوبت پزشکی:
دکتر: {doctor_name}
تاریخ: {appointment_date}
ساعت: {appointment_time}
مکان: {clinic_name}

برای لغو یا تغییر نوبت با ما تماس بگیرید.
دکتر ترن"""
        
        return message.strip()
    
    def _get_2_hour_reminder_message(self, reservation) -> str:
        """Generate 2-hour reminder message"""
        patient_name = reservation.patient.name if reservation.patient else "عزیز"
        doctor_name = reservation.doctor.user.get_full_name()
        appointment_time = reservation.time.strftime('%H:%M')
        clinic_address = reservation.doctor.clinic.address if reservation.doctor.clinic else ""
        
        message = f"""سلام {patient_name}
نوبت شما تا ۲ ساعت دیگر:
دکتر: {doctor_name}
ساعت: {appointment_time}
آدرس: {clinic_address}

لطفاً به موقع حاضر شوید.
دکتر ترن"""
        
        return message.strip()
    
    def _get_general_reminder_message(self, reservation, hours_before: int) -> str:
        """Generate general reminder message"""
        patient_name = reservation.patient.name if reservation.patient else "عزیز"
        doctor_name = reservation.doctor.user.get_full_name()
        appointment_date = reservation.day.date.strftime('%Y/%m/%d')
        appointment_time = reservation.time.strftime('%H:%M')
        
        message = f"""سلام {patient_name}
یادآوری نوبت پزشکی:
دکتر: {doctor_name}
تاریخ: {appointment_date}
ساعت: {appointment_time}

{hours_before} ساعت تا نوبت شما باقی مانده.
دکتر ترن"""
        
        return message.strip()
    
    def _get_confirmation_message(self, reservation) -> str:
        """Generate confirmation message"""
        patient_name = reservation.patient.name if reservation.patient else "عزیز"
        doctor_name = reservation.doctor.user.get_full_name()
        appointment_date = reservation.day.date.strftime('%Y/%m/%d')
        appointment_time = reservation.time.strftime('%H:%M')
        
        message = f"""سلام {patient_name}
نوبت شما با موفقیت ثبت شد:
دکتر: {doctor_name}
تاریخ: {appointment_date}
ساعت: {appointment_time}

کد پیگیری: {reservation.id}
دکتر ترن"""
        
        return message.strip()
    
    def _get_cancellation_message(self, reservation) -> str:
        """Generate cancellation message"""
        patient_name = reservation.patient.name if reservation.patient else "عزیز"
        doctor_name = reservation.doctor.user.get_full_name()
        appointment_date = reservation.day.date.strftime('%Y/%m/%d')
        appointment_time = reservation.time.strftime('%H:%M')
        
        message = f"""سلام {patient_name}
نوبت شما لغو شد:
دکتر: {doctor_name}
تاریخ: {appointment_date}
ساعت: {appointment_time}

برای رزرو مجدد به سایت مراجعه کنید.
دکتر ترن"""
        
        return message.strip()


# Create a singleton instance
sms_service = SMSService()


# Convenience functions for backward compatibility
def send_sms(number: str, message: str) -> Dict[str, Any]:
    """
    Convenience function for sending SMS
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


def send_verification_code(phone_number: str, template_id: int = None) -> tuple:
    """Convenience function for sending verification codes"""
    return sms_service.send_verification_code(phone_number, template_id) 