from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
import jdatetime

from .models import Reservation, ReservationDay
from doctors.models import Doctor
from patients.models import PatientsFile
from wallet.models import Wallet, Transaction
from payments.models import PaymentRequest, PaymentGateway

User = get_user_model()


class ReservationPaymentTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            phone='09123456789',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create doctor
        self.doctor = Doctor.objects.create(
            user=User.objects.create_user(
                phone='09123456788',
                email='doctor@example.com',
                password='doctorpass123',
                first_name='Dr.',
                last_name='Test'
            ),
            specialization='Cardiology',
            consultation_fee=Decimal('50000'),
            is_available=True
        )
        
        # Create patient file
        self.patient = PatientsFile.objects.create(
            user=self.user,
            phone='09123456789',
            email='test@example.com',
            national_id='1234567890'
        )
        
        # Create wallet
        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('100000')  # 100,000 tomans
        )
        
        # Create reservation day
        tomorrow = timezone.now().date() + timezone.timedelta(days=1)
        self.reservation_day = ReservationDay.objects.create(
            date=tomorrow,
            published=True
        )
        
        # Create available reservation slot
        self.reservation = Reservation.objects.create(
            day=self.reservation_day,
            doctor=self.doctor,
            time='09:00:00',
            status='available',
            payment_status='pending',
            amount=Decimal('50000')  # 50,000 tomans
        )
        
        # Create payment gateway
        self.gateway = PaymentGateway.objects.create(
            name='Test Gateway',
            gateway_type='zarinpal',
            merchant_id='test-merchant',
            callback_url='http://localhost:8000/payments/callback/',
            is_active=True,
            is_sandbox=True
        )
        
        # Create client
        self.client = Client()

    def test_wallet_payment_sufficient_balance(self):
        """Test wallet payment when user has sufficient balance"""
        patient_data = {
            'name': 'Test User',
            'phone': '09123456789',
            'national_id': '1234567890',
            'email': 'test@example.com'
        }
        
        # Test wallet payment
        success, message = self.reservation.book_appointment(
            patient_data=patient_data,
            user=self.user,
            payment_method='wallet'
        )
        
        self.assertTrue(success)
        self.assertIn('موفقیت', message)
        
        # Check reservation status
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'confirmed')
        self.assertEqual(self.reservation.payment_status, 'paid')
        self.assertIsNotNone(self.reservation.transaction)
        
        # Check wallet balance
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('50000'))  # 100,000 - 50,000
        
        # Check transaction
        transaction = self.reservation.transaction
        self.assertEqual(transaction.amount, Decimal('50000'))
        self.assertEqual(transaction.transaction_type, 'payment')
        self.assertEqual(transaction.status, 'completed')

    def test_wallet_payment_insufficient_balance(self):
        """Test wallet payment when user has insufficient balance"""
        # Set low balance
        self.wallet.balance = Decimal('20000')  # 20,000 tomans
        self.wallet.save()
        
        patient_data = {
            'name': 'Test User',
            'phone': '09123456789',
            'national_id': '1234567890',
            'email': 'test@example.com'
        }
        
        # Test wallet payment
        success, message = self.reservation.book_appointment(
            patient_data=patient_data,
            user=self.user,
            payment_method='wallet'
        )
        
        self.assertFalse(success)
        self.assertIn('موجودی کیف پول کافی نیست', message)
        
        # Check reservation status (should remain unchanged)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'available')
        self.assertEqual(self.reservation.payment_status, 'pending')

    def test_direct_payment_booking(self):
        """Test direct payment booking"""
        patient_data = {
            'name': 'Test User',
            'phone': '09123456789',
            'national_id': '1234567890',
            'email': 'test@example.com'
        }
        
        # Test direct payment booking
        success, message = self.reservation.book_with_direct_payment(
            patient_data=patient_data,
            user=self.user
        )
        
        self.assertTrue(success)
        self.assertIn('لطفاً پرداخت خود را تکمیل کنید', message)
        
        # Check reservation status
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'pending')
        self.assertEqual(self.reservation.payment_status, 'pending')
        self.assertIsNone(self.reservation.transaction)
        
        # Check patient data was saved
        self.assertEqual(self.reservation.patient_name, 'Test User')
        self.assertEqual(self.reservation.phone, '09123456789')

    def test_payment_choice_view(self):
        """Test payment choice view"""
        # Set low balance to trigger payment choice
        self.wallet.balance = Decimal('20000')
        self.wallet.save()
        
        # Login user
        self.client.force_login(self.user)
        
        # Access payment choice page
        url = reverse('reservations:payment_choice', args=[self.reservation.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'انتخاب روش پرداخت')
        self.assertContains(response, 'شارژ کیف پول')
        self.assertContains(response, 'پرداخت مستقیم')

    def test_process_payment_choice_wallet_charge(self):
        """Test processing wallet charge choice"""
        # Set low balance
        self.wallet.balance = Decimal('20000')
        self.wallet.save()
        
        # Login user
        self.client.force_login(self.user)
        
        # Process wallet charge choice
        url = reverse('reservations:process_payment_choice', args=[self.reservation.id])
        response = self.client.post(url, {
            'payment_choice': 'wallet_charge',
            'suggested_amount': '50000'
        })
        
        # Should redirect to wallet deposit
        self.assertEqual(response.status_code, 302)
        self.assertIn('wallet/deposit', response.url)

    def test_process_payment_choice_direct_payment(self):
        """Test processing direct payment choice"""
        # Set low balance
        self.wallet.balance = Decimal('20000')
        self.wallet.save()
        
        # Login user
        self.client.force_login(self.user)
        
        # Store pending booking data in session
        session = self.client.session
        session['pending_booking_data'] = {
            'doctor_id': self.doctor.id,
            'date': '1403/01/01',
            'time': '09:00',
            'patient_data': {
                'name': 'Test User',
                'phone': '09123456789',
                'national_id': '1234567890',
                'email': 'test@example.com'
            },
            'reservation_id': self.reservation.id
        }
        session.save()
        
        # Process direct payment choice
        url = reverse('reservations:process_payment_choice', args=[self.reservation.id])
        response = self.client.post(url, {
            'payment_choice': 'direct_payment'
        })
        
        # Should redirect to payment page
        self.assertEqual(response.status_code, 302)
        self.assertIn('payments/reservation_payment', response.url)
        
        # Check reservation was booked with direct payment
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'pending')
        self.assertEqual(self.reservation.payment_status, 'pending')

    def test_book_appointment_view_with_direct_payment(self):
        """Test booking appointment view with direct payment method"""
        # Login user
        self.client.force_login(self.user)
        
        # Book appointment with direct payment
        url = reverse('reservations:book_appointment', args=[self.doctor.id])
        response = self.client.post(url, {
            'date': self.reservation_day.date.strftime('%Y/%m/%d'),
            'time': '09:00',
            'patient_name': 'Test',
            'patient_last_name': 'User',
            'patient_national_id': '1234567890',
            'patient_email': 'test@example.com',
            'phone': '09123456789',
            'payment_method': 'direct'
        })
        
        # Should redirect to payment page
        self.assertEqual(response.status_code, 302)
        self.assertIn('payments/reservation_payment', response.url)

    def test_book_appointment_view_with_wallet_payment(self):
        """Test booking appointment view with wallet payment method"""
        # Login user
        self.client.force_login(self.user)
        
        # Book appointment with wallet payment
        url = reverse('reservations:book_appointment', args=[self.doctor.id])
        response = self.client.post(url, {
            'date': self.reservation_day.date.strftime('%Y/%m/%d'),
            'time': '09:00',
            'patient_name': 'Test',
            'patient_last_name': 'User',
            'patient_national_id': '1234567890',
            'patient_email': 'test@example.com',
            'phone': '09123456789',
            'payment_method': 'wallet'
        })
        
        # Should redirect to view appointment page
        self.assertEqual(response.status_code, 302)
        self.assertIn('reservations/view', response.url)

    def test_payment_callback_reservation_completion(self):
        """Test payment callback for reservation completion"""
        # Create a pending reservation with direct payment
        patient_data = {
            'name': 'Test User',
            'phone': '09123456789',
            'national_id': '1234567890',
            'email': 'test@example.com'
        }
        
        success, message = self.reservation.book_with_direct_payment(
            patient_data=patient_data,
            user=self.user
        )
        
        # Create payment request
        payment_request = PaymentRequest.objects.create(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('50000'),
            description='Test payment',
            gateway=self.gateway,
            authority='test-authority',
            metadata={
                'type': 'reservation_payment',
                'reservation_id': self.reservation.id
            }
        )
        
        # Simulate successful payment callback
        self.client.force_login(self.user)
        url = reverse('payments:payment_callback')
        response = self.client.get(url, {
            'Authority': 'test-authority',
            'Status': 'OK'
        })
        
        # Should redirect to view appointment
        self.assertEqual(response.status_code, 302)
        self.assertIn('reservations/view', response.url)
        
        # Check reservation was confirmed
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'confirmed')
        self.assertEqual(self.reservation.payment_status, 'paid')
