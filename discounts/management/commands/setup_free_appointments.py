from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from discounts.models import Discount, DiscountType, AutomaticDiscount


class Command(BaseCommand):
    help = 'Setup first two appointments free discount'

    def handle(self, *args, **options):
        # Create or get the discount type for percentage discount
        discount_type, created = DiscountType.objects.get_or_create(
            name='100% تخفیف',
            defaults={
                'type': 'percentage',
                'description': 'تخفیف کامل برای نوبت‌های رایگان',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created discount type: {discount_type.name}')
            )
        
        # Create or get the 100% discount
        discount, created = Discount.objects.get_or_create(
            title='دو نوبت اول رایگان',
            defaults={
                'description': 'دو نوبت اول هر کاربر به صورت رایگان',
                'discount_type': discount_type,
                'percentage': 100,
                'applicable_to': 'all',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=365*10),  # 10 years validity
                'usage_limit_per_user': 2,
                'status': 'active',
                'is_public': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created discount: {discount.title}')
            )
        
        # Create or update automatic discount
        automatic_discount, created = AutomaticDiscount.objects.get_or_create(
            name='دو نوبت اول رایگان',
            defaults={
                'discount': discount,
                'is_first_appointment': False,
                'max_free_appointments': 2,
                'is_active': True
            }
        )
        
        if not created:
            # Update existing automatic discount
            automatic_discount.discount = discount
            automatic_discount.is_first_appointment = False
            automatic_discount.max_free_appointments = 2
            automatic_discount.is_active = True
            automatic_discount.save()
            self.stdout.write(self.style.SUCCESS(f'Updated automatic discount: {automatic_discount.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Created automatic discount: {automatic_discount.name}'))
        
        self.stdout.write(
            self.style.SUCCESS(
                'Successfully set up first two appointments free discount system!'
            )
        ) 