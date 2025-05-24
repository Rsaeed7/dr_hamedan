from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from discounts.models import DiscountType, Discount, CouponCode, AutomaticDiscount
from doctors.models import Doctor, Specialization
from user.models import User


class Command(BaseCommand):
    help = 'Create sample discount data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample discount data...')
        
        # Create discount types
        percentage_type, created = DiscountType.objects.get_or_create(
            type='percentage',
            defaults={
                'name': 'تخفیف درصدی',
                'description': 'تخفیف بر اساس درصد از مبلغ کل'
            }
        )
        
        fixed_amount_type, created = DiscountType.objects.get_or_create(
            type='fixed_amount',
            defaults={
                'name': 'تخفیف مبلغ ثابت',
                'description': 'تخفیف با مبلغ ثابت'
            }
        )
        
        # Get admin user for created_by field
        admin_user = User.objects.filter(is_superuser=True).first()
        
        # Create sample discounts
        discounts_data = [
            {
                'title': 'تخفیف ۲۰ درصدی ویژه',
                'description': 'تخفیف ۲۰ درصدی برای همه خدمات پزشکی',
                'discount_type': percentage_type,
                'percentage': Decimal('20.00'),
                'applicable_to': 'all',
                'min_amount': Decimal('100000'),
                'max_discount_amount': Decimal('50000'),
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=30),
                'usage_limit': 100,
                'usage_limit_per_user': 1,
                'created_by': admin_user
            },
            {
                'title': 'تخفیف ۵۰ هزار تومانی',
                'description': 'تخفیف ۵۰ هزار تومانی برای نوبت‌های بالای ۲۰۰ هزار تومان',
                'discount_type': fixed_amount_type,
                'fixed_amount': Decimal('50000'),
                'applicable_to': 'all',
                'min_amount': Decimal('200000'),
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=60),
                'usage_limit': 50,
                'usage_limit_per_user': 2,
                'created_by': admin_user
            },
            {
                'title': 'تخفیف ویژه بیماران جدید',
                'description': 'تخفیف ۱۵ درصدی برای اولین نوبت',
                'discount_type': percentage_type,
                'percentage': Decimal('15.00'),
                'applicable_to': 'first_time',
                'max_discount_amount': Decimal('30000'),
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=90),
                'created_by': admin_user
            },
            {
                'title': 'تخفیف وفاداری',
                'description': 'تخفیف ۱۰ درصدی برای بیماران قدیمی',
                'discount_type': percentage_type,
                'percentage': Decimal('10.00'),
                'applicable_to': 'returning',
                'max_discount_amount': Decimal('25000'),
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=45),
                'usage_limit_per_user': 3,
                'created_by': admin_user
            }
        ]
        
        created_discounts = []
        for discount_data in discounts_data:
            discount, created = Discount.objects.get_or_create(
                title=discount_data['title'],
                defaults=discount_data
            )
            if created:
                created_discounts.append(discount)
                self.stdout.write(f'✓ Created discount: {discount.title}')
            else:
                self.stdout.write(f'- Discount already exists: {discount.title}')
        
        # Create coupon codes for some discounts
        coupon_codes_data = [
            {'code': 'WELCOME20', 'discount': created_discounts[0] if created_discounts else Discount.objects.first()},
            {'code': 'SAVE50K', 'discount': created_discounts[1] if len(created_discounts) > 1 else Discount.objects.first()},
            {'code': 'NEWPATIENT', 'discount': created_discounts[2] if len(created_discounts) > 2 else Discount.objects.first()},
            {'code': 'LOYALTY10', 'discount': created_discounts[3] if len(created_discounts) > 3 else Discount.objects.first()},
        ]
        
        for coupon_data in coupon_codes_data:
            if coupon_data['discount']:
                coupon, created = CouponCode.objects.get_or_create(
                    code=coupon_data['code'],
                    defaults={'discount': coupon_data['discount']}
                )
                if created:
                    self.stdout.write(f'✓ Created coupon code: {coupon.code}')
                else:
                    self.stdout.write(f'- Coupon code already exists: {coupon.code}')
        
        # Create automatic discounts
        if created_discounts:
            # First appointment automatic discount
            auto_discount_1, created = AutomaticDiscount.objects.get_or_create(
                name='تخفیف خودکار اولین نوبت',
                defaults={
                    'discount': created_discounts[2] if len(created_discounts) > 2 else created_discounts[0],
                    'is_first_appointment': True
                }
            )
            if created:
                self.stdout.write('✓ Created automatic discount for first appointments')
            
            # Weekend automatic discount
            weekend_discount_data = {
                'title': 'تخفیف آخر هفته',
                'description': 'تخفیف ۵ درصدی برای نوبت‌های آخر هفته',
                'discount_type': percentage_type,
                'percentage': Decimal('5.00'),
                'applicable_to': 'all',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=365),
                'created_by': admin_user
            }
            
            weekend_discount, created = Discount.objects.get_or_create(
                title=weekend_discount_data['title'],
                defaults=weekend_discount_data
            )
            
            auto_discount_2, created = AutomaticDiscount.objects.get_or_create(
                name='تخفیف خودکار آخر هفته',
                defaults={
                    'discount': weekend_discount,
                    'is_weekend': True
                }
            )
            if created:
                self.stdout.write('✓ Created automatic discount for weekends')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSample discount data created successfully!\n'
                f'Created {len(created_discounts)} new discounts.\n'
                f'You can now test the discount system.'
            )
        )
        
        # Display coupon codes for testing
        self.stdout.write('\n' + '='*50)
        self.stdout.write('COUPON CODES FOR TESTING:')
        self.stdout.write('='*50)
        for coupon in CouponCode.objects.filter(is_active=True):
            self.stdout.write(f'Code: {coupon.code} - {coupon.discount.title}')
        self.stdout.write('='*50) 