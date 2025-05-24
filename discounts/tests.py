from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from .models import (
    DiscountType, Discount, CouponCode, DiscountUsage, 
    AutomaticDiscount, DiscountReport
)
from doctors.models import Doctor, Specialization
from user.models import User
from reservations.models import Reservation, ReservationDay
from patients.models import PatientsFile
from clinics.models import Clinic
from django.urls import reverse
import json

User = get_user_model()


class DiscountModelTests(TestCase):
    def setUp(self):
        # ایجاد کاربر
        self.user = User.objects.create_user(
            phone='09123456789',
            first_name='تست',
            last_name='کاربر',
            password='testpass123'
        )
        
        # ایجاد تخصص
        self.specialization = Specialization.objects.create(
            name='قلب و عروق',
            description='تخصص قلب و عروق'
        )
        
        # ایجاد پزشک
        self.doctor_user = User.objects.create_user(
            phone='09123456788',
            first_name='دکتر',
            last_name='تست',
            password='testpass123'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization=self.specialization,
            license_number='12345'
        )
        
        # ایجاد نوع تخفیف
        self.discount_type = DiscountType.objects.create(
            name='درصدی',
            type='percentage'
        )
        
    def test_discount_creation(self):
        """تست ایجاد تخفیف"""
        discount = Discount.objects.create(
            title='تخفیف تست',
            description='توضیحات تست',
            discount_type=self.discount_type,
            percentage=Decimal('20.00'),
            applicable_to='all',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            created_by=self.user
        )
        self.assertEqual(discount.title, 'تخفیف تست')
        self.assertEqual(discount.percentage, Decimal('20.00'))
        
    def test_coupon_code_creation(self):
        """تست ایجاد کد تخفیف"""
        discount = Discount.objects.create(
            title='تخفیف تست',
            description='توضیحات تست',
            discount_type=self.discount_type,
            percentage=Decimal('15.00'),
            applicable_to='all',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            created_by=self.user
        )
        
        coupon = CouponCode.objects.create(
            code='TEST15',
            discount=discount
        )
        self.assertEqual(coupon.code, 'TEST15')
        self.assertEqual(coupon.discount, discount)
        
    def test_discount_calculation_percentage(self):
        """تست محاسبه تخفیف درصدی"""
        discount = Discount.objects.create(
            title='تخفیف درصدی',
            description='توضیحات تست',
            discount_type=self.discount_type,
            percentage=Decimal('20.00'),
            applicable_to='all',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            created_by=self.user
        )
        
        amount = Decimal('100000')
        discount_amount = discount.calculate_discount(amount)
        self.assertEqual(discount_amount, Decimal('20000'))
        
    def test_discount_calculation_fixed(self):
        """تست محاسبه تخفیف مبلغ ثابت"""
        fixed_type = DiscountType.objects.create(
            name='مبلغ ثابت',
            type='fixed_amount'
        )
        
        discount = Discount.objects.create(
            title='تخفیف ثابت',
            description='توضیحات تست',
            discount_type=fixed_type,
            fixed_amount=Decimal('50000'),
            applicable_to='all',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            created_by=self.user
        )
        
        amount = Decimal('200000')
        discount_amount = discount.calculate_discount(amount)
        self.assertEqual(discount_amount, Decimal('50000'))
        
    def test_max_discount_amount(self):
        """تست حداکثر مبلغ تخفیف"""
        discount = Discount.objects.create(
            title='تخفیف با حداکثر',
            description='توضیحات تست',
            discount_type=self.discount_type,
            percentage=Decimal('50.00'),
            max_discount_amount=Decimal('30000'),
            applicable_to='all',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            created_by=self.user
        )
        
        amount = Decimal('100000')
        discount_amount = discount.calculate_discount(amount)
        self.assertEqual(discount_amount, Decimal('30000'))
        
    def test_discount_validity(self):
        """تست اعتبار تخفیف"""
        # تخفیف معتبر
        valid_discount = Discount.objects.create(
            title='تخفیف معتبر',
            description='توضیحات تست',
            discount_type=self.discount_type,
            percentage=Decimal('10.00'),
            applicable_to='all',
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30),
            status='active',
            created_by=self.user
        )
        self.assertTrue(valid_discount.is_valid())
        
        # تخفیف منقضی
        expired_discount = Discount.objects.create(
            title='تخفیف منقضی',
            description='توضیحات تست',
            discount_type=self.discount_type,
            percentage=Decimal('10.00'),
            applicable_to='all',
            start_date=timezone.now() - timedelta(days=30),
            end_date=timezone.now() - timedelta(days=1),
            status='active',
            created_by=self.user
        )
        self.assertFalse(expired_discount.is_valid())


class AutomaticDiscountTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='09123456789',
            first_name='تست',
            last_name='کاربر',
            password='testpass123'
        )
        
        # ایجاد تخصص
        self.specialization = Specialization.objects.create(
            name='قلب و عروق',
            description='تخصص قلب و عروق'
        )
        
        self.doctor_user = User.objects.create_user(
            phone='09123456788',
            first_name='دکتر',
            last_name='تست',
            password='testpass123'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization=self.specialization,
            license_number='12345'
        )
        
        self.discount_type = DiscountType.objects.create(
            name='درصدی',
            type='percentage'
        )
        
        self.discount = Discount.objects.create(
            title='تخفیف اولین نوبت',
            description='توضیحات تست',
            discount_type=self.discount_type,
            percentage=Decimal('30.00'),
            applicable_to='first_time',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            created_by=self.user
        )
        
    def test_first_appointment_discount(self):
        """تست تخفیف اولین نوبت"""
        auto_discount = AutomaticDiscount.objects.create(
            name='تخفیف اولین نوبت',
            discount=self.discount,
            is_first_appointment=False
        )
        
        self.assertEqual(auto_discount.name, 'تخفیف اولین نوبت')
        self.assertFalse(auto_discount.is_first_appointment)


class DiscountReportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='09123456789',
            first_name='تست',
            last_name='کاربر',
            password='testpass123'
        )
        
        # ایجاد تخصص
        self.specialization = Specialization.objects.create(
            name='قلب و عروق',
            description='تخصص قلب و عروق'
        )
        
        self.discount_type = DiscountType.objects.create(
            name='درصدی',
            type='percentage'
        )
        
        self.discount = Discount.objects.create(
            title='تخفیف تست',
            description='توضیحات تست',
            discount_type=self.discount_type,
            percentage=Decimal('20.00'),
            applicable_to='all',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            created_by=self.user
        )
        
    def test_discount_report_generation(self):
        """تست تولید گزارش تخفیف"""
        report = DiscountReport.objects.create(
            discount=self.discount,
            period_start=timezone.now().date(),
            period_end=timezone.now().date() + timedelta(days=30),
            total_usage_count=10,
            total_discount_amount=Decimal('200000')
        )
        
        self.assertEqual(report.total_usage_count, 10)
        self.assertEqual(report.total_discount_amount, Decimal('200000'))


class DiscountIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='09123456789',
            first_name='تست',
            last_name='کاربر',
            password='testpass123'
        )
        
        # ایجاد تخصص
        self.specialization = Specialization.objects.create(
            name='قلب و عروق',
            description='تخصص قلب و عروق'
        )
        
        self.doctor_user = User.objects.create_user(
            phone='09123456788',
            first_name='دکتر',
            last_name='تست',
            password='testpass123'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization=self.specialization,
            license_number='12345'
        )
        
        self.discount_type = DiscountType.objects.create(
            name='درصدی',
            type='percentage'
        )
        
        self.discount = Discount.objects.create(
            title='تخفیف محدود',
            description='توضیحات تست',
            discount_type=self.discount_type,
            percentage=Decimal('25.00'),
            applicable_to='all',
            usage_limit=1,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            created_by=self.user
        )
        
    def test_discount_usage_limit(self):
        """تست محدودیت استفاده از تخفیف"""
        # اولین استفاده
        self.assertTrue(self.discount.can_be_used_by_user(self.user))
        
        # شبیه‌سازی استفاده
        self.discount.used_count = 1
        self.discount.save()
        
        # بررسی عدم امکان استفاده مجدد
        self.assertFalse(self.discount.is_valid())


class FirstTwoAppointmentsFreeTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            phone='09123456789',
            first_name='علی',
            last_name='احمدی'
        )
        
        # Create patient profile
        self.patient = PatientsFile.objects.create(
            user=self.user,
            phone='09123456789',
            national_id='1234567890',
            birthdate=timezone.now().date() - timedelta(days=365*25),
            gender='male'
        )
        
        # Create admin user for clinic
        self.admin_user = User.objects.create_user(
            phone='09123456787',
            first_name='ادمین',
            last_name='کلینیک'
        )
        
        # Create clinic
        self.clinic = Clinic.objects.create(
            name='کلینیک تست',
            address='تهران',
            phone='02112345678',
            email='test@clinic.com',
            admin=self.admin_user
        )
        
        # Create specialization
        self.specialization = Specialization.objects.create(
            name='پزشک عمومی'
        )
        
        # Create doctor
        self.doctor = Doctor.objects.create(
            user=User.objects.create_user(
                phone='09123456788',
                first_name='دکتر',
                last_name='محمدی'
            ),
            specialization=self.specialization,
            clinic=self.clinic,
            license_number='12345',
            consultation_fee=100000,
            phone='02112345679'
        )
        
        # Create a reservation day
        self.reservation_day = ReservationDay.objects.create(
            date=date.today(),
            published=True
        )
        
        # Set up discount system (this should already be done by the management command)
        self.discount_type = DiscountType.objects.get_or_create(
            name='100% تخفیف',
            defaults={
                'type': 'percentage',
                'description': 'تخفیف کامل برای نوبت‌های رایگان',
                'is_active': True
            }
        )[0]
        
        self.discount = Discount.objects.get_or_create(
            title='دو نوبت اول رایگان',
            defaults={
                'description': 'دو نوبت اول هر کاربر به صورت رایگان',
                'discount_type': self.discount_type,
                'percentage': 100,
                'applicable_to': 'all',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=365*10),
                'usage_limit_per_user': 2,
                'status': 'active',
                'is_public': True
            }
        )[0]
        
        self.automatic_discount = AutomaticDiscount.objects.get_or_create(
            name='دو نوبت اول رایگان',
            defaults={
                'discount': self.discount,
                'is_first_appointment': False,
                'max_free_appointments': 2,
                'is_active': True
            }
        )[0]
    
    def test_first_appointment_gets_discount(self):
        """Test that the first appointment gets 100% discount"""
        # Create first reservation
        reservation1 = Reservation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            day=self.reservation_day,
            time='10:00',
            phone='09123456789',
            amount=self.doctor.consultation_fee,
            status='pending'
        )
        
        # Check if automatic discount applies
        applies = self.automatic_discount.check_conditions(reservation1, self.user)
        self.assertTrue(applies, "First appointment should qualify for automatic discount")
        
        # Apply the discount
        success, message = self.discount.apply_to_reservation(reservation1, self.user)
        self.assertTrue(success, f"Discount should apply successfully: {message}")
        
        # Check that discount was applied
        self.assertTrue(hasattr(reservation1, 'discount_usage'))
        discount_usage = reservation1.discount_usage
        self.assertEqual(discount_usage.discount_amount, self.doctor.consultation_fee)
        self.assertEqual(discount_usage.final_amount, 0)
    
    def test_second_appointment_gets_discount(self):
        """Test that the second appointment also gets 100% discount"""
        # Create first reservation (completed)
        reservation1 = Reservation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            day=self.reservation_day,
            time='10:00',
            phone='09123456789',
            amount=self.doctor.consultation_fee,
            status='completed',
            payment_status='paid'
        )
        
        # Create second reservation
        reservation2 = Reservation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            day=self.reservation_day,
            time='11:00',
            phone='09123456789',
            amount=self.doctor.consultation_fee,
            status='pending'
        )
        
        # Check if automatic discount applies to second appointment
        applies = self.automatic_discount.check_conditions(reservation2, self.user)
        self.assertTrue(applies, "Second appointment should qualify for automatic discount")
        
        # Apply the discount
        success, message = self.discount.apply_to_reservation(reservation2, self.user)
        self.assertTrue(success, f"Discount should apply to second appointment: {message}")
        
        # Check that discount was applied
        self.assertTrue(hasattr(reservation2, 'discount_usage'))
        discount_usage = reservation2.discount_usage
        self.assertEqual(discount_usage.discount_amount, self.doctor.consultation_fee)
        self.assertEqual(discount_usage.final_amount, 0)
    
    def test_third_appointment_no_discount(self):
        """Test that the third appointment does not get discount"""
        # Create a reservation day for this test
        day = ReservationDay.objects.create(
            date=date.today(),
            published=True
        )
        
        # Create first reservation (completed)
        reservation1 = Reservation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            day=day,
            time='10:00',
            phone='09123456789',
            amount=self.doctor.consultation_fee,
            status='completed',
            payment_status='paid'
        )
        
        # Create second reservation (completed)
        reservation2 = Reservation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            day=day,
            time='11:00',
            phone='09123456789',
            amount=self.doctor.consultation_fee,
            status='completed',
            payment_status='paid'
        )
        
        # Create third reservation
        reservation3 = Reservation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            day=day,
            time='12:00',
            phone='09123456789',
            amount=self.doctor.consultation_fee,
            status='pending'
        )
        
        # Check if automatic discount applies to third appointment
        applies = self.automatic_discount.check_conditions(reservation3, self.user)
        self.assertFalse(applies, "Third appointment should NOT qualify for automatic discount")
        
        # Try to apply the discount (should fail)
        success, message = self.discount.apply_to_reservation(reservation3, self.user)
        self.assertFalse(success, "Discount should not apply to third appointment")
    
    def test_discount_usage_limit_per_user(self):
        """Test that the discount respects the usage limit per user"""
        # Create first reservation
        reservation1 = Reservation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            day=self.reservation_day,
            time='10:00',
            phone='09123456789',
            amount=self.doctor.consultation_fee,
            status='pending'
        )
        
        # Apply discount to first reservation
        applicable_discounts = self.automatic_discount.check_conditions(reservation1, self.user)
        self.assertTrue(applicable_discounts)
        
        # Mark first reservation as completed
        reservation1.status = 'completed'
        reservation1.payment_status = 'paid'
        reservation1.save()
        
        # Create second reservation
        reservation2 = Reservation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            day=self.reservation_day,
            time='11:00',
            phone='09123456789',
            amount=self.doctor.consultation_fee,
            status='pending'
        )
        
        # Apply discount to second reservation
        applicable_discounts = self.automatic_discount.check_conditions(reservation2, self.user)
        self.assertTrue(applicable_discounts)
        
        # Mark second reservation as completed
        reservation2.status = 'completed'
        reservation2.payment_status = 'paid'
        reservation2.save()
        
        # Create third reservation
        reservation3 = Reservation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            day=self.reservation_day,
            time='12:00',
            phone='09123456789',
            amount=self.doctor.consultation_fee,
            status='pending'
        )
        
        # Third reservation should not get discount
        applicable_discounts = self.automatic_discount.check_conditions(reservation3, self.user)
        self.assertFalse(applicable_discounts)


class DiscountIntegrationTestCase(TestCase):
    """Integration test for the complete discount flow"""
    
    def setUp(self):
        """Set up test data for integration testing"""
        # Create admin user
        self.admin_user = User.objects.create_user(
            phone='09123456700',
            first_name='ادمین',
            last_name='سیستم',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create patient user
        self.user = User.objects.create_user(
            phone='09123456789',
            first_name='بیمار',
            last_name='تست',
            password='testpass123'
        )
        
        # Create patient profile
        self.patient = PatientsFile.objects.create(
            user=self.user,
            phone='09123456789',
            national_id='1234567890',
            birthdate=date(1990, 1, 1),
            gender='male'
        )
        
        # Create specialization
        self.specialization = Specialization.objects.create(
            name='قلب و عروق',
            description='تخصص قلب و عروق'
        )
        
        # Create clinic
        self.clinic = Clinic.objects.create(
            name='کلینیک تست',
            address='آدرس تست',
            phone='02112345678',
            admin=self.admin_user
        )
        
        # Create doctor user
        self.doctor_user = User.objects.create_user(
            phone='09123456788',
            first_name='دکتر',
            last_name='تست',
            password='testpass123'
        )
        
        # Create doctor
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization=self.specialization,
            license_number='12345',
            consultation_fee=200000,
            clinic=self.clinic
        )
        
        # Create reservation day
        self.reservation_day = ReservationDay.objects.create(
            date=date.today(),
            published=True
        )
        
        # Set up discount system
        self.discount_type = DiscountType.objects.get_or_create(
            name='100% تخفیف',
            defaults={
                'type': 'percentage',
                'description': 'تخفیف کامل برای نوبت‌های رایگان',
                'is_active': True
            }
        )[0]
        
        self.discount = Discount.objects.get_or_create(
            title='دو نوبت اول رایگان',
            defaults={
                'description': 'دو نوبت اول هر کاربر به صورت رایگان',
                'discount_type': self.discount_type,
                'percentage': 100,
                'applicable_to': 'all',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=365*10),
                'usage_limit_per_user': 2,
                'status': 'active',
                'is_public': True,
                'created_by': self.admin_user
            }
        )[0]
        
        self.automatic_discount = AutomaticDiscount.objects.get_or_create(
            name='دو نوبت اول رایگان',
            defaults={
                'discount': self.discount,
                'is_first_appointment': False,
                'max_free_appointments': 2,
                'is_active': True
            }
        )[0]
    
    def test_complete_discount_flow_first_appointment(self):
        """Test the complete discount flow for the first appointment"""
        # Login the user
        self.client.login(phone='09123456789', password='testpass123')
        
        # Create first reservation
        reservation = Reservation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            day=self.reservation_day,
            time='10:00',
            phone='09123456789',
            amount=self.doctor.consultation_fee,
            status='pending'
        )
        
        # Test the check_automatic_discounts view
        response = self.client.post(
            reverse('discounts:check_automatic_discounts'),
            data=json.dumps({'reservation_id': reservation.id}),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['discount_title'], 'دو نوبت اول رایگان')
        self.assertEqual(data['discount_amount'], float(self.doctor.consultation_fee))
        self.assertEqual(data['final_amount'], 0.0)
        self.assertEqual(data['original_amount'], float(self.doctor.consultation_fee))
        
        # Verify reservation was updated
        reservation.refresh_from_db()
        self.assertEqual(reservation.amount, 0)
        self.assertTrue(hasattr(reservation, 'discount_usage'))
        
        # Verify discount usage record
        discount_usage = reservation.discount_usage
        self.assertEqual(discount_usage.discount, self.discount)
        self.assertEqual(discount_usage.user, self.user)
        self.assertEqual(discount_usage.discount_amount, self.doctor.consultation_fee)
        self.assertEqual(discount_usage.final_amount, 0)
    
    def test_complete_discount_flow_second_appointment(self):
        """Test the complete discount flow for the second appointment"""
        # Login the user
        self.client.login(phone='09123456789', password='testpass123')
        
        # Create and complete first reservation
        reservation1 = Reservation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            day=self.reservation_day,
            time='10:00',
            phone='09123456789',
            amount=self.doctor.consultation_fee,
            status='completed',
            payment_status='paid'
        )
        
        # Create second reservation
        reservation2 = Reservation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            day=self.reservation_day,
            time='11:00',
            phone='09123456789',
            amount=self.doctor.consultation_fee,
            status='pending'
        )
        
        # Test the check_automatic_discounts view for second appointment
        response = self.client.post(
            reverse('discounts:check_automatic_discounts'),
            data=json.dumps({'reservation_id': reservation2.id}),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['discount_title'], 'دو نوبت اول رایگان')
        self.assertEqual(data['discount_amount'], float(self.doctor.consultation_fee))
        self.assertEqual(data['final_amount'], 0.0)
        
        # Verify reservation was updated
        reservation2.refresh_from_db()
        self.assertEqual(reservation2.amount, 0)
        self.assertTrue(hasattr(reservation2, 'discount_usage'))
    
    def test_complete_discount_flow_third_appointment_no_discount(self):
        """Test that the third appointment does not get discount through the view"""
        # Login the user
        self.client.login(phone='09123456789', password='testpass123')
        
        # Create and complete first two reservations
        reservation1 = Reservation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            day=self.reservation_day,
            time='10:00',
            phone='09123456789',
            amount=self.doctor.consultation_fee,
            status='completed',
            payment_status='paid'
        )
        
        reservation2 = Reservation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            day=self.reservation_day,
            time='11:00',
            phone='09123456789',
            amount=self.doctor.consultation_fee,
            status='completed',
            payment_status='paid'
        )
        
        # Create third reservation
        reservation3 = Reservation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            day=self.reservation_day,
            time='12:00',
            phone='09123456789',
            amount=self.doctor.consultation_fee,
            status='pending'
        )
        
        # Test the check_automatic_discounts view for third appointment
        response = self.client.post(
            reverse('discounts:check_automatic_discounts'),
            data=json.dumps({'reservation_id': reservation3.id}),
            content_type='application/json'
        )
        
        # Check response - should not apply discount
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('تخفیف خودکاری یافت نشد', data['message'])
        
        # Verify reservation was not updated
        reservation3.refresh_from_db()
        self.assertEqual(reservation3.amount, self.doctor.consultation_fee)
        self.assertFalse(hasattr(reservation3, 'discount_usage'))
    
    def test_get_available_discounts_view(self):
        """Test the get_available_discounts view"""
        # Login the user
        self.client.login(phone='09123456789', password='testpass123')
        
        # Create reservation
        reservation = Reservation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            day=self.reservation_day,
            time='10:00',
            phone='09123456789',
            amount=self.doctor.consultation_fee,
            status='pending'
        )
        
        # Test the get_available_discounts view
        response = self.client.get(
            reverse('discounts:get_available_discounts'),
            {'reservation_id': reservation.id}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIsInstance(data['discounts'], list)
        
        # Should include our discount
        discount_found = False
        for discount_data in data['discounts']:
            if discount_data['title'] == 'دو نوبت اول رایگان':
                discount_found = True
                self.assertEqual(discount_data['discount_amount'], float(self.doctor.consultation_fee))
                break
        
        self.assertTrue(discount_found, "The 'دو نوبت اول رایگان' discount should be available")
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access discount endpoints"""
        # Create reservation
        reservation = Reservation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            day=self.reservation_day,
            time='10:00',
            phone='09123456789',
            amount=self.doctor.consultation_fee,
            status='pending'
        )
        
        # Test without login
        response = self.client.post(
            reverse('discounts:check_automatic_discounts'),
            data=json.dumps({'reservation_id': reservation.id}),
            content_type='application/json'
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_invalid_reservation_id(self):
        """Test handling of invalid reservation ID"""
        # Login the user
        self.client.login(phone='09123456789', password='testpass123')
        
        # Test with non-existent reservation ID
        response = self.client.post(
            reverse('discounts:check_automatic_discounts'),
            data=json.dumps({'reservation_id': 99999}),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('رزرو یافت نشد', data['message']) 