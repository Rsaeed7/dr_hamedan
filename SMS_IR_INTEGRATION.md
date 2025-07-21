# SMS.ir Integration Documentation - Dr. Turn Platform

## Overview
This document describes the complete integration of SMS.ir API for all SMS functionality in the Dr. Turn doctor appointment booking system.

## Integration Summary

### 1. Centralized SMS Service
All SMS functionality is now handled through a single centralized service located at `utils/sms_service.py`. This service uses the SMS.ir API for:

- **User Authentication**: OTP verification for login/registration
- **Appointment Reminders**: 24-hour and 2-hour reminders
- **Appointment Confirmations**: Immediate confirmation after booking
- **Appointment Cancellations**: Notification when appointments are cancelled
- **Doctor Approvals**: Credentials sent when doctor registration is approved

### 2. SMS.ir API Configuration

#### Settings (in `dr_turn/settings.py`):
```python
SMS_API_KEY = 'wZYwHS1oPJTV5pJ8SJUkdfrZf7Vh2iFzFN84sdUPc9bjE4s8fE6BN8k0KzNm4e1Y'
SMS_LINE_NUMBER = '30007487130094'
SMS_OTP_TEMPLATE_ID = 100000  # Template ID for OTP verification
SMS_REMINDER_ENABLED = True
```

### 3. SMS Types and Methods

#### A. Verification Code (OTP)
Uses SMS.ir's **Verify API** with templates for secure OTP delivery:
```python
from utils.sms_service import sms_service

# Send OTP
message, status_code, otp_code = sms_service.send_verification_code(
    phone_number='09123456789',
    template_id=100000  # Optional, uses default if not provided
)
```

#### B. Regular SMS Messages
Uses SMS.ir's **Bulk API** for appointment reminders and notifications:
```python
# Send regular SMS
result = sms_service.send_sms(
    number='09123456789',
    message='Your appointment reminder message'
)
```

### 4. Integration Points

#### User Registration/Login (`user/views.py`)
- Replaced old SMS provider with SMS.ir
- Uses verify API with template for OTP
- Automatic code generation with security (replaces 0 with 5)

#### Appointment Reminders (`sms_reminders/services.py`)
- Automated scheduling for 24h and 2h reminders
- Working hours consideration
- Retry mechanism for failed messages

#### Doctor Registration Approval (`doctors/models.py`)
- Sends credentials via SMS when approved
- Uses regular SMS API for notifications

### 5. SMS Templates

#### OTP Template (ID: 100000)
```
کد تایید شما: {Code}
```

#### Appointment Confirmation
```
سلام {patient_name}
نوبت شما با موفقیت ثبت شد:
دکتر: {doctor_name}
تاریخ: {appointment_date}
ساعت: {appointment_time}
کد پیگیری: {reservation_id}
دکتر ترن
```

#### 24-Hour Reminder
```
سلام {patient_name}
یادآوری نوبت پزشکی:
دکتر: {doctor_name}
تاریخ: {appointment_date}
ساعت: {appointment_time}
مکان: {clinic_name}

برای لغو یا تغییر نوبت با ما تماس بگیرید.
دکتر ترن
```

#### 2-Hour Reminder
```
سلام {patient_name}
نوبت شما تا ۲ ساعت دیگر:
دکتر: {doctor_name}
ساعت: {appointment_time}
آدرس: {clinic_address}

لطفاً به موقع حاضر شوید.
دکتر ترن
```

### 6. Testing

#### Send Test SMS
```bash
python manage.py send_test_sms 09123456789 --message "Test message"
```

#### Test OTP Sending
```python
from utils.sms_service import sms_service

message, status_code, code = sms_service.send_verification_code('09123456789')
print(f"Status: {status_code}, Message: {message}, Code: {code}")
```

### 7. Error Handling

The system includes comprehensive error handling:
- Service availability checks
- API response validation
- Logging for debugging
- User-friendly error messages in Persian

### 8. Security Considerations

- OTP codes are 6 digits with 0 replaced by 5
- Codes expire after 2 minutes
- API keys stored in settings (should use environment variables in production)
- Rate limiting handled by SMS.ir

### 9. Monitoring and Logs

All SMS activities are logged:
- Successful sends logged at INFO level
- Failures logged at ERROR level with details
- SMS reminder system maintains its own database logs
# test
### 10. Future Enhancements

1. **Template Management**: Create admin interface for SMS templates
2. **Analytics Dashboard**: Track SMS usage and costs
3. **Multi-provider Support**: Add fallback SMS providers
4. **Batch Sending**: Optimize for bulk notifications
5. **Template Variables**: More dynamic template system

## Troubleshooting

### Common Issues

1. **SMS Not Sending**
   - Check SMS_REMINDER_ENABLED is True
   - Verify API key and line number
   - Check SMS.ir account balance

2. **OTP Not Working**
   - Verify template ID is correct
   - Check template is approved in SMS.ir panel
   - Ensure phone number format is correct (09xxxxxxxxx)

3. **Reminders Not Sent**
   - Run `python manage.py process_sms_reminders`
   - Check cron job is configured
   - Verify working hours settings

### Support

For SMS.ir API issues: https://sms.ir/support
For system issues: Contact development team

## Conclusion

The SMS.ir integration provides a robust, centralized SMS solution for all communication needs in the Dr. Turn platform. The system is production-ready with comprehensive error handling, logging, and monitoring capabilities. 