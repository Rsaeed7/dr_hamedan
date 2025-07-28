from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from payments.models import PaymentGateway, PaymentRequest
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the payment system to ensure it works correctly'

    def handle(self, *args, **options):
        self.stdout.write('Testing payment system...')
        
        # Check if payment gateway exists
        try:
            gateway = PaymentGateway.objects.filter(
                gateway_type='zarinpal',
                is_active=True
            ).first()
            
            if not gateway:
                self.stdout.write(
                    self.style.ERROR('No active ZarinPal gateway found. Run setup_zarinpal_gateway first.')
                )
                return
            
            self.stdout.write(
                self.style.SUCCESS(f'Found active gateway: {gateway.name}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error checking payment gateway: {e}')
            )
            return
        
        # Test PaymentRequest creation
        try:
            # Get first user
            user = User.objects.first()
            if not user:
                self.stdout.write(
                    self.style.ERROR('No users found in database.')
                )
                return
            
            # Create a test payment request
            payment_request = PaymentRequest.objects.create(
                user=user,
                amount=Decimal('1000'),
                description='Test payment request',
                gateway=gateway
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created PaymentRequest: {payment_request.id}')
            )
            
            # Test status change
            payment_request.status = 'processing'
            payment_request.save()
            
            self.stdout.write(
                self.style.SUCCESS('Successfully updated PaymentRequest status')
            )
            
            # Test mark as failed
            payment_request.mark_as_failed('Test failure')
            
            self.stdout.write(
                self.style.SUCCESS('Successfully marked payment as failed')
            )
            
            # Clean up
            payment_request.delete()
            
            self.stdout.write(
                self.style.SUCCESS('Payment system test completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error testing PaymentRequest: {e}')
            )
            return 