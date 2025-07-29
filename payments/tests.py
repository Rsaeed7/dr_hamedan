from django.test import TestCase
from django.contrib.auth import get_user_model
from .services import CurrencyConverter, PaymentService
from .models import PaymentGateway, PaymentRequest
from wallet.models import Wallet

User = get_user_model()


class CurrencyConverterTest(TestCase):
    """تست تبدیل واحد پول"""
    
    def test_toman_to_rial_conversion(self):
        """تست تبدیل تومان به ریال"""
        # Test basic conversion
        self.assertEqual(CurrencyConverter.toman_to_rial(1000), 10000)
        self.assertEqual(CurrencyConverter.toman_to_rial(50000), 500000)
        self.assertEqual(CurrencyConverter.toman_to_rial(100000), 1000000)
        
        # Test edge cases
        self.assertEqual(CurrencyConverter.toman_to_rial(1), 10)
        self.assertEqual(CurrencyConverter.toman_to_rial(0), 0)
    
    def test_rial_to_toman_conversion(self):
        """تست تبدیل ریال به تومان"""
        # Test basic conversion
        self.assertEqual(CurrencyConverter.rial_to_toman(10000), 1000)
        self.assertEqual(CurrencyConverter.rial_to_toman(500000), 50000)
        self.assertEqual(CurrencyConverter.rial_to_toman(1000000), 100000)
        
        # Test edge cases
        self.assertEqual(CurrencyConverter.rial_to_toman(10), 1)
        self.assertEqual(CurrencyConverter.rial_to_toman(0), 0)
        
        # Test rounding (should round down)
        self.assertEqual(CurrencyConverter.rial_to_toman(15), 1)  # 15/10 = 1.5 -> 1
        self.assertEqual(CurrencyConverter.rial_to_toman(19), 1)  # 19/10 = 1.9 -> 1
    
    def test_conversion_consistency(self):
        """تست سازگاری تبدیل‌ها"""
        original_amount = 50000  # 50,000 تومان
        
        # Convert to Rial and back to Toman
        rial_amount = CurrencyConverter.toman_to_rial(original_amount)
        back_to_toman = CurrencyConverter.rial_to_toman(rial_amount)
        
        # Should get the same amount back (or very close due to rounding)
        self.assertEqual(back_to_toman, original_amount)


class PaymentServiceTest(TestCase):
    """تست سرویس پرداخت"""
    
    def setUp(self):
        """تنظیمات اولیه"""
        # Create test user
        self.user = User.objects.create_user(
            phone='09123456789',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create wallet
        self.wallet = Wallet.objects.create(user=self.user, balance=100000)
        
        # Create payment gateway
        self.gateway = PaymentGateway.objects.create(
            name='Test Gateway',
            gateway_type='zarinpal',
            merchant_id='test-merchant',
            callback_url='http://example.com/callback',
            min_amount=1000,
            max_amount=50000000,
            is_active=True,
            is_sandbox=True
        )
    
    def test_payment_amount_storage(self):
        """تست ذخیره مبلغ به تومان در دیتابیس"""
        # Create a payment request with amount in Toman
        payment_request = PaymentRequest.objects.create(
            user=self.user,
            wallet=self.wallet,
            amount=50000,  # 50,000 تومان
            description='Test payment',
            gateway=self.gateway
        )
        
        # Verify amount is stored as Toman
        self.assertEqual(payment_request.amount, 50000)
        
        # Verify conversion to Rial for gateway
        rial_amount = CurrencyConverter.toman_to_rial(payment_request.amount)
        self.assertEqual(rial_amount, 500000)  # 500,000 ریال 