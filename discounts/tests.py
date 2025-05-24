from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import (
    DiscountType, Discount, CouponCode, DiscountUsage, 
    AutomaticDiscount, DiscountReport
)
from doctors.models import Doctor, Specialization
from user.models import User

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
            is_first_appointment=True
        )
        
        self.assertEqual(auto_discount.name, 'تخفیف اولین نوبت')
        self.assertTrue(auto_discount.is_first_appointment)


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