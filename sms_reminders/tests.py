from django.test import TestCase
from django.utils import timezone
from django.core.management import call_command
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json
from io import StringIO

from reservations.models import Reservation, ReservationDay
from doctors.models import Doctor, Specialization
from patients.models import PatientsFile
from clinics.models import Clinic
from .models import SMSReminder, SMSReminderSettings, SMSReminderTemplate, SMSLog
from .services import SMSReminderService, schedule_appointment_reminders, send_confirmation_sms, send_cancellation_sms
from user.models import User

User = get_user_model()


class SMSReminderModelTest(TestCase):
    """Test SMS reminder models"""
    
    def setUp(self):
        # Create test users
        self.doctor_user = User.objects.create_user(
            phone='09123456789',
            password='testpass123',
            first_name='Test',
            last_name='Doctor',
            email='doctor@test.com'
        )
        
        self.patient_user = User.objects.create_user(
            phone='09987654321',
            password='testpass123',
            first_name='Test',
            last_name='Patient',
            email='patient@test.com'
        )
        
        # Create specialization
        self.specialization = Specialization.objects.create(
            name='General Medicine',
            description='General medical practice'
        )
        
        # Create clinic
        self.clinic = Clinic.objects.create(
            name='Test Clinic',
            address='Test Address',
            phone='02112345678',
            email='clinic@example.com',
            admin=self.doctor_user
        )
        
        # Create doctor
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            clinic=self.clinic,
            specialization=self.specialization,
            license_number='12345',
            phone='09123456789'
        )
        
        # Create patient
        self.patient = PatientsFile.objects.create(
            user=self.patient_user,
            phone='09987654321'
        )
        
        # Create reservation day
        self.reservation_day = ReservationDay.objects.create(
            date=timezone.now().date() + timedelta(days=1),
            published=True
        )
        
        # Create reservation
        self.reservation = Reservation.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            day=self.reservation_day,
            time=timezone.now().time(),
            phone='09987654321',
            status='confirmed',
            payment_status='paid',
            amount=100000
        )
    
    def test_sms_reminder_creation(self):
        """Test SMS reminder model creation"""
        reminder = SMSReminder.objects.create(
            reservation=self.reservation,
            user=self.doctor_user,
            reminder_type='confirmation',
            phone_number='09123456789',
            message='Test message',
            scheduled_time=timezone.now()
        )
        
        self.assertEqual(reminder.status, 'pending')
        self.assertEqual(reminder.attempts, 0)
        self.assertEqual(reminder.max_attempts, 3)
        
        # Test can_retry when status is failed
        reminder.status = 'failed'
        reminder.save()
        self.assertTrue(reminder.can_retry())
    
    def test_sms_reminder_mark_as_sent(self):
        """Test marking reminder as sent"""
        reminder = SMSReminder.objects.create(
            reservation=self.reservation,
            user=self.doctor_user,
            reminder_type='confirmation',
            phone_number='09123456789',
            message='Test message',
            scheduled_time=timezone.now()
        )
        
        response_data = {'status': 'success', 'id': '12345'}
        reminder.mark_as_sent(response_data)
        
        self.assertEqual(reminder.status, 'sent')
        self.assertIsNotNone(reminder.sent_time)
        self.assertEqual(reminder.sms_response, response_data)
    
    def test_sms_reminder_mark_as_failed(self):
        """Test marking reminder as failed"""
        reminder = SMSReminder.objects.create(
            reservation=self.reservation,
            user=self.doctor_user,
            reminder_type='confirmation',
            phone_number='09123456789',
            message='Test message',
            scheduled_time=timezone.now()
        )
        
        reminder.mark_as_failed('Test error')
        
        self.assertEqual(reminder.status, 'failed')
        self.assertEqual(reminder.attempts, 1)
        self.assertEqual(reminder.error_message, 'Test error')
    
    def test_sms_reminder_settings(self):
        """Test SMS reminder settings"""
        settings = SMSReminderSettings.get_settings()
        
        self.assertTrue(settings.reminder_24h_enabled)
        self.assertTrue(settings.reminder_2h_enabled)
        self.assertTrue(settings.confirmation_sms_enabled)
        self.assertEqual(settings.max_retry_attempts, 3)
    
    def test_sms_reminder_template(self):
        """Test SMS reminder template"""
        template = SMSReminderTemplate.objects.create(
            name='Test Template',
            reminder_type='confirmation',
            template='Hello {patient_name}, your appointment with {doctor_name} is confirmed.',
            is_active=True
        )
        
        message = template.render_message(self.reservation)
        self.assertIn('Test Doctor', message)
        self.assertIn('09987654321', message)  # Patient phone number will be in the name


class SMSReminderServiceTest(TestCase):
    """Test SMS reminder service"""
    
    def setUp(self):
        # Create test data (same as above)
        self.doctor_user = User.objects.create_user(
            phone='09123456789',
            password='testpass123',
            first_name='Test',
            last_name='Doctor',
            email='doctor@test.com'
        )
        
        self.patient_user = User.objects.create_user(
            phone='09987654321',
            password='testpass123',
            first_name='Test',
            last_name='Patient',
            email='patient@test.com'
        )
        
        # Create specialization
        self.specialization = Specialization.objects.create(
            name='General Medicine',
            description='General medical practice'
        )
        
        # Create clinic
        self.clinic = Clinic.objects.create(
            name='Test Clinic',
            address='Test Address',
            phone='02112345678',
            email='clinic@example.com',
            admin=self.doctor_user
        )
        
        # Create doctor
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            clinic=self.clinic,
            specialization=self.specialization,
            license_number='12345',
            phone='09123456789'
        )
        
        # Create patient
        self.patient = PatientsFile.objects.create(
            user=self.patient_user,
            phone='09987654321'
        )
        
        # Create reservation day
        self.reservation_day = ReservationDay.objects.create(
            date=timezone.now().date() + timedelta(days=2),
            published=True
        )
        
        future_time = (timezone.now() + timedelta(hours=25)).time()
        self.reservation = Reservation.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            day=self.reservation_day,
            time=future_time,
            phone='09987654321',
            status='confirmed',
            payment_status='paid',
            amount=100000
        )
        
        self.service = SMSReminderService()
    
    def test_schedule_appointment_reminders(self):
        """Test scheduling appointment reminders"""
        reminders = self.service.schedule_appointment_reminders(self.reservation)
        
        # Should create 2 reminders (24h and 2h)
        self.assertEqual(len(reminders), 2)
        
        reminder_types = [r.reminder_type for r in reminders]
        self.assertIn('reminder_24h', reminder_types)
        self.assertIn('reminder_2h', reminder_types)
    
    @patch('sms_reminders.services.sms_service.send_sms')
    def test_send_confirmation_sms(self, mock_send_sms):
        """Test sending confirmation SMS"""
        mock_send_sms.return_value = {
            'success': True,
            'message': 'SMS sent successfully',
            'response': {'status_code': 200, 'json': {'id': '12345'}}
        }
        
        reminder = self.service.send_confirmation_sms(self.reservation)
        
        self.assertIsNotNone(reminder)
        self.assertEqual(reminder.reminder_type, 'confirmation')
        self.assertEqual(reminder.status, 'sent')
        mock_send_sms.assert_called_once()
    
    @patch('sms_reminders.services.sms_service.send_sms')
    def test_send_cancellation_sms(self, mock_send_sms):
        """Test sending cancellation SMS"""
        mock_send_sms.return_value = {
            'success': True,
            'message': 'SMS sent successfully',
            'response': {'status_code': 200, 'json': {'id': '12345'}}
        }
        
        reminder = self.service.send_cancellation_sms(self.reservation)
        
        self.assertIsNotNone(reminder)
        self.assertEqual(reminder.reminder_type, 'cancellation')
        self.assertEqual(reminder.status, 'sent')
        mock_send_sms.assert_called_once()
    
    @patch('sms_reminders.services.sms_service.send_sms')
    def test_process_pending_reminders(self, mock_send_sms):
        """Test processing pending reminders"""
        mock_send_sms.return_value = {
            'success': True,
            'message': 'SMS sent successfully',
            'response': {'status_code': 200, 'json': {'id': '12345'}}
        }
        
        # Create a pending reminder scheduled within working hours
        now = timezone.now()
        # Set time to 10:00 AM to ensure it's within working hours (8:00-20:00)
        scheduled_time = now.replace(hour=10, minute=0, second=0, microsecond=0) - timedelta(minutes=1)
        
        reminder = SMSReminder.objects.create(
            reservation=self.reservation,
            user=self.doctor_user,
            reminder_type='reminder_24h',
            phone_number='09123456789',
            message='Test reminder',
            scheduled_time=scheduled_time
        )
        
        result = self.service.process_pending_reminders()
        
        self.assertEqual(result['sent'], 1)
        self.assertEqual(result['failed'], 0)
        
        reminder.refresh_from_db()
        self.assertEqual(reminder.status, 'sent')
    
    def test_cancel_reminders_for_reservation(self):
        """Test canceling reminders for a reservation"""
        # Create some reminders
        SMSReminder.objects.create(
            reservation=self.reservation,
            user=self.doctor_user,
            reminder_type='reminder_24h',
            phone_number='09123456789',
            message='Test reminder 1',
            scheduled_time=timezone.now() + timedelta(hours=23)
        )
        
        SMSReminder.objects.create(
            reservation=self.reservation,
            user=self.doctor_user,
            reminder_type='reminder_2h',
            phone_number='09123456789',
            message='Test reminder 2',
            scheduled_time=timezone.now() + timedelta(hours=1)
        )
        
        cancelled_count = self.service.cancel_reminders_for_reservation(self.reservation)
        
        self.assertEqual(cancelled_count, 2)
        
        # Check that reminders are cancelled
        reminders = SMSReminder.objects.filter(reservation=self.reservation)
        for reminder in reminders:
            self.assertEqual(reminder.status, 'cancelled')


class SMSReminderManagementCommandTest(TestCase):
    """Test SMS reminder management commands"""
    
    def setUp(self):
        # Create test data
        self.doctor_user = User.objects.create_user(
            phone='09123456789',
            password='testpass123',
            first_name='Test',
            last_name='Doctor',
            email='doctor@test.com'
        )
        
        self.patient_user = User.objects.create_user(
            phone='09987654321',
            password='testpass123',
            first_name='Test',
            last_name='Patient',
            email='patient@test.com'
        )
        
        # Create specialization
        self.specialization = Specialization.objects.create(
            name='General Medicine',
            description='General medical practice'
        )
        
        # Create clinic
        self.clinic = Clinic.objects.create(
            name='Test Clinic',
            address='Test Address',
            phone='02112345678',
            email='clinic@example.com',
            admin=self.doctor_user
        )
        
        # Create doctor
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            clinic=self.clinic,
            specialization=self.specialization,
            license_number='12345',
            phone='09123456789'
        )
        
        # Create patient
        self.patient = PatientsFile.objects.create(
            user=self.patient_user,
            phone='09987654321'
        )
        
        # Create reservation day
        self.reservation_day = ReservationDay.objects.create(
            date=timezone.now().date() + timedelta(days=1),
            published=True
        )
        
        self.reservation = Reservation.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            day=self.reservation_day,
            time=timezone.now().time(),
            phone='09987654321',
            status='confirmed',
            payment_status='paid',
            amount=100000
        )
    
    @patch('sms_reminders.services.sms_service.send_sms')
    def test_process_sms_reminders_command(self, mock_send_sms):
        """Test process_sms_reminders management command"""
        mock_send_sms.return_value = {
            'success': True,
            'message': 'SMS sent successfully',
            'response': {'status_code': 200, 'json': {'id': '12345'}}
        }
        
        # Create a pending reminder scheduled within working hours
        now = timezone.now()
        scheduled_time = now.replace(hour=10, minute=0, second=0, microsecond=0)
        
        SMSReminder.objects.create(
            reservation=self.reservation,
            user=self.doctor_user,
            reminder_type='reminder_24h',
            phone_number='09123456789',
            message='Test reminder',
            scheduled_time=scheduled_time
        )
        
        # Run the command
        call_command('process_sms_reminders')
        
        # Check that the reminder was processed
        reminder = SMSReminder.objects.get(reservation=self.reservation)
        self.assertEqual(reminder.status, 'sent')
    
    def test_cleanup_old_reminders_command(self):
        """Test cleanup_old_reminders management command"""
        # Create old reminders
        old_time = timezone.now() - timedelta(days=31)
        
        SMSReminder.objects.create(
            reservation=self.reservation,
            user=self.doctor_user,
            reminder_type='confirmation',
            phone_number='09123456789',
            message='Old reminder',
            scheduled_time=old_time,
            status='sent',
            sent_time=old_time
        )
        
        # Run the command
        call_command('cleanup_old_reminders')
        
        # Check that old reminders were deleted
        old_reminders = SMSReminder.objects.filter(created_at__lt=timezone.now() - timedelta(days=30))
        self.assertEqual(old_reminders.count(), 0)


class SMSLogTest(TestCase):
    """Test SMS log functionality"""
    
    def setUp(self):
        self.doctor_user = User.objects.create_user(
            phone='09123456789',
            password='testpass123',
            first_name='Test',
            last_name='Doctor',
            email='doctor@test.com'
        )
        
        self.patient_user = User.objects.create_user(
            phone='09987654321',
            password='testpass123',
            first_name='Test',
            last_name='Patient',
            email='patient@test.com'
        )
        
        # Create specialization
        self.specialization = Specialization.objects.create(
            name='General Medicine',
            description='General medical practice'
        )
        
        # Create clinic
        self.clinic = Clinic.objects.create(
            name='Test Clinic',
            address='Test Address',
            phone='02112345678',
            email='clinic@example.com',
            admin=self.doctor_user
        )
        
        # Create doctor
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            clinic=self.clinic,
            specialization=self.specialization,
            license_number='12345',
            phone='09123456789'
        )
        
        # Create patient
        self.patient = PatientsFile.objects.create(
            user=self.patient_user,
            phone='09987654321'
        )
        
        # Create reservation day
        self.reservation_day = ReservationDay.objects.create(
            date=timezone.now().date() + timedelta(days=1),
            published=True
        )
        
        self.reservation = Reservation.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            day=self.reservation_day,
            time=timezone.now().time(),
            phone='09987654321',
            status='confirmed',
            payment_status='paid',
            amount=100000
        )
    
    def test_sms_log_creation(self):
        """Test SMS log creation"""
        reminder = SMSReminder.objects.create(
            reservation=self.reservation,
            user=self.doctor_user,
            reminder_type='confirmation',
            phone_number='09123456789',
            message='Test message',
            scheduled_time=timezone.now()
        )
        
        log = SMSLog.objects.create(
            phone_number='09123456789',
            message='Test message',
            reminder=reminder,
            success=True,
            response_data={'status': 'sent', 'id': '12345'}
        )
        
        self.assertEqual(log.phone_number, '09123456789')
        self.assertTrue(log.success)
        self.assertEqual(log.response_data['status'], 'sent')
        self.assertEqual(log.reminder, reminder)


class ConvenienceFunctionTest(TestCase):
    """Test convenience functions"""
    
    def setUp(self):
        self.doctor_user = User.objects.create_user(
            phone='09123456789',
            password='testpass123',
            first_name='Test',
            last_name='Doctor',
            email='doctor@test.com'
        )
        
        self.patient_user = User.objects.create_user(
            phone='09987654321',
            password='testpass123',
            first_name='Test',
            last_name='Patient',
            email='patient@test.com'
        )
        
        # Create specialization
        self.specialization = Specialization.objects.create(
            name='General Medicine',
            description='General medical practice'
        )
        
        # Create clinic
        self.clinic = Clinic.objects.create(
            name='Test Clinic',
            address='Test Address',
            phone='02112345678',
            email='clinic@example.com',
            admin=self.doctor_user
        )
        
        # Create doctor
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            clinic=self.clinic,
            specialization=self.specialization,
            license_number='12345',
            phone='09123456789'
        )
        
        # Create patient
        self.patient = PatientsFile.objects.create(
            user=self.patient_user,
            phone='09987654321'
        )
        
        # Create reservation day
        self.reservation_day = ReservationDay.objects.create(
            date=timezone.now().date() + timedelta(days=2),
            published=True
        )
        
        future_time = (timezone.now() + timedelta(hours=25)).time()
        self.reservation = Reservation.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            day=self.reservation_day,
            time=future_time,
            phone='09987654321',
            status='confirmed',
            payment_status='paid',
            amount=100000
        )
    
    def test_schedule_appointment_reminders_function(self):
        """Test schedule_appointment_reminders convenience function"""
        reminders = schedule_appointment_reminders(self.reservation)
        
        self.assertEqual(len(reminders), 2)
        self.assertTrue(all(isinstance(r, SMSReminder) for r in reminders))
    
    @patch('sms_reminders.services.sms_service.send_sms')
    def test_send_confirmation_sms_function(self, mock_send_sms):
        """Test send_confirmation_sms convenience function"""
        mock_send_sms.return_value = {
            'success': True,
            'message': 'SMS sent successfully',
            'response': {'status_code': 200, 'json': {'id': '12345'}}
        }
        
        reminder = send_confirmation_sms(self.reservation)
        
        self.assertIsNotNone(reminder)
        self.assertEqual(reminder.reminder_type, 'confirmation')
        self.assertEqual(reminder.status, 'sent')
