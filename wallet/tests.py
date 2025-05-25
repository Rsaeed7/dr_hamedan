from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch, Mock
import json
import django_jalali
from django_jalali.db import models as jmodels
import jdatetime

from .models import Wallet, Transaction, PaymentGateway
from reservations.models import Reservation, ReservationDay
from patients.models import PatientsFile
from doctors.models import Doctor, Specialization
from clinics.models import Clinic

User = get_user_model()


class WalletModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='09123456789',
            password='testpass123',
            first_name='تست',
            last_name='کاربر'
        )
        self.wallet = Wallet.objects.create(user=self.user)

    def test_wallet_creation(self):
        """تست ایجاد کیف پول"""
        self.assertEqual(self.wallet.balance, Decimal('0.00'))
        self.assertEqual(self.wallet.pending_balance, Decimal('0.00'))
        self.assertEqual(self.wallet.frozen_balance, Decimal('0.00'))
        self.assertTrue(self.wallet.is_active)

    def test_add_balance(self):
        """تست افزودن موجودی"""
        self.wallet.add_balance(Decimal('1000.00'))
        self.assertEqual(self.wallet.balance, Decimal('1000.00'))

    def test_subtract_balance(self):
        """تست کسر موجودی"""
        self.wallet.add_balance(Decimal('1000.00'))
        result = self.wallet.subtract_balance(Decimal('500.00'))
        self.assertTrue(result)
        self.assertEqual(self.wallet.balance, Decimal('500.00'))

    def test_subtract_balance_insufficient(self):
        """تست کسر موجودی با موجودی ناکافی"""
        result = self.wallet.subtract_balance(Decimal('500.00'))
        self.assertFalse(result)
        self.assertEqual(self.wallet.balance, Decimal('0.00'))

    def test_freeze_balance(self):
        """تست مسدود کردن موجودی"""
        self.wallet.add_balance(Decimal('1000.00'))
        result = self.wallet.freeze_balance(Decimal('300.00'))
        self.assertTrue(result)
        self.assertEqual(self.wallet.balance, Decimal('700.00'))
        self.assertEqual(self.wallet.frozen_balance, Decimal('300.00'))

    def test_unfreeze_balance(self):
        """تست آزاد کردن موجودی مسدود"""
        self.wallet.add_balance(Decimal('1000.00'))
        self.wallet.freeze_balance(Decimal('300.00'))
        result = self.wallet.unfreeze_balance(Decimal('300.00'))
        self.assertTrue(result)
        self.assertEqual(self.wallet.balance, Decimal('1000.00'))
        self.assertEqual(self.wallet.frozen_balance, Decimal('0.00'))


class TransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='09123456789',
            password='testpass123',
            first_name='تست',
            last_name='کاربر'
        )
        self.wallet = Wallet.objects.create(user=self.user)
        self.gateway = PaymentGateway.objects.create(
            name='درگاه تست',
            code='test',
            api_key='test_key',
            merchant_id='test_merchant',
            gateway_url='https://test.com/pay',
            verify_url='https://test.com/verify'
        )

    def test_transaction_creation(self):
        """تست ایجاد تراکنش"""
        transaction = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('1000.00'),
            transaction_type='deposit',
            gateway=self.gateway
        )
        self.assertEqual(transaction.status, 'pending')
        self.assertEqual(transaction.amount, Decimal('1000.00'))

    def test_mark_as_completed(self):
        """تست تکمیل تراکنش"""
        transaction = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('1000.00'),
            transaction_type='deposit',
            gateway=self.gateway
        )
        transaction.mark_as_completed()
        self.assertEqual(transaction.status, 'completed')
        self.assertIsNotNone(transaction.processed_at)

    def test_mark_as_failed(self):
        """تست شکست تراکنش"""
        transaction = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('1000.00'),
            transaction_type='deposit',
            gateway=self.gateway
        )
        transaction.mark_as_failed()
        self.assertEqual(transaction.status, 'failed')
        self.assertIsNotNone(transaction.processed_at)


class WalletViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='09123456789',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(phone='09123456789', password='testpass123')
        
        # Create wallet for user
        self.wallet = Wallet.objects.create(user=self.user)
        
        # Create payment gateway
        self.gateway = PaymentGateway.objects.create(
            name='Test Gateway',
            code='test',
            api_key='test_key',
            merchant_id='test_merchant',
            is_active=True
        )
        
        # Create specialization and clinic for reservation
        self.specialization = Specialization.objects.create(name='Test Specialty')
        
        # Create admin user for clinic
        self.admin_user = User.objects.create_user(
            phone='09987654321',
            password='testpass123'
        )
        
        self.clinic = Clinic.objects.create(
            name='Test Clinic',
            address='Test Address',
            phone='02112345678',
            email='test@clinic.com',
            admin=self.admin_user
        )
        
        # Create doctor
        self.doctor = Doctor.objects.create(
            user=self.user,
            specialization=self.specialization,
            license_number='12345'
        )
        
        # Create reservation day and reservation
        self.reservation_day = ReservationDay.objects.create(
            date=jdatetime.date.today(),
            published=True
        )
        
        # Create a PatientsFile for the reservation
        self.patient_file = PatientsFile.objects.create(
            user=self.user,
            phone='09123456789'
        )
        
        self.reservation = Reservation.objects.create(
            day=self.reservation_day,
            patient=self.patient_file,
            doctor=self.doctor,
            time=timezone.now().time(),
            phone='09123456789',
            amount=Decimal('100000'),
            status='pending'
        )

    def test_wallet_dashboard_view(self):
        """تست نمایش داشبورد کیف پول"""
        response = self.client.get(reverse('wallet:wallet_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'کیف پول')
        self.assertIn('wallet', response.context)

    def test_transaction_list_view(self):
        """تست نمایش لیست تراکنش‌ها"""
        # Create a test transaction
        Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            amount=50000,
            transaction_type='deposit',
            status='completed'
        )
        
        response = self.client.get(reverse('wallet:transaction_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'تاریخچه تراکنش‌ها')

    def test_deposit_view_get(self):
        """تست نمایش صفحه واریز"""
        response = self.client.get(reverse('wallet:deposit'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'افزودن موجودی')

    def test_deposit_view_post(self):
        """تست واریز وجه"""
        response = self.client.post(reverse('wallet:deposit'), {
            'amount': '100000',
            'payment_gateway': self.gateway.id,
            'description': 'Test deposit'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to payment
        
        # Check transaction was created
        transaction = Transaction.objects.filter(wallet=self.wallet).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, Decimal('100000'))

    def test_process_payment_view(self):
        """تست پردازش پرداخت"""
        # Add balance to wallet first
        self.wallet.add_balance(Decimal('200000'))
        
        response = self.client.post(reverse('wallet:process_payment', kwargs={'reservation_id': self.reservation.id}), {
            'amount': '100000',
            'payment_method': 'wallet'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after processing

    def test_payment_callback_success(self):
        """Test successful payment callback"""
        # Create a test transaction
        transaction = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            amount=100000,
            transaction_type='payment',
            gateway=self.gateway,
            authority='test_authority_123'
        )
        
        # Simulate successful callback
        response = self.client.post(reverse('wallet:payment_callback'), {
            'Authority': 'test_authority_123',
            'Status': 'OK'
        })
        
        # Check transaction status after callback
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'completed')


class PaymentGatewayTest(TestCase):
    def setUp(self):
        self.gateway = PaymentGateway.objects.create(
            name='درگاه تست',
            code='test',
            api_key='test_key',
            merchant_id='test_merchant',
            gateway_url='https://test.com/pay',
            verify_url='https://test.com/verify',
            commission_percentage=Decimal('2.5')
        )

    def test_calculate_commission(self):
        """تست محاسبه کمیسیون"""
        amount = Decimal('10000')
        commission = self.gateway.calculate_commission(amount)
        expected = amount * self.gateway.commission_percentage / 100
        self.assertEqual(commission, expected)

    def test_gateway_str_representation(self):
        """تست نمایش رشته‌ای درگاه"""
        self.assertEqual(str(self.gateway), 'درگاه تست')


class WalletIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='09123456789',
            password='testpass123',
            first_name='تست',
            last_name='کاربر'
        )
        self.wallet = Wallet.objects.create(user=self.user)

    def test_deposit_and_payment_flow(self):
        """تست جریان کامل واریز و پرداخت"""
        # واریز اولیه
        deposit_transaction = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('100000'),
            transaction_type='deposit'
        )
        deposit_transaction.mark_as_completed()
        
        # پرداخت
        payment_amount = Decimal('50000')
        payment_transaction = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            amount=payment_amount,
            transaction_type='payment'
        )
        payment_transaction.mark_as_completed()
        
        # بررسی موجودی نهایی
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('50000'))
