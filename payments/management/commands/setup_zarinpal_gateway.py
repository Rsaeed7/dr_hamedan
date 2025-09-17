from django.core.management.base import BaseCommand
from payments.models import PaymentGateway
from django.conf import settings


class Command(BaseCommand):
    help = 'Set up ZarinPal payment gateway for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--merchant-id',
            type=str,
            default='228ddf66-9aee-4fce-bf09-53872c308402',
            help='ZarinPal merchant ID'
        )
        parser.add_argument(
            '--sandbox',
            action='store_true',
            help='Use sandbox environment'
        )
        parser.add_argument(
            '--callback-url',
            type=str,
            default='http://localhost:8000/payments/callback/',
            help='Callback URL for payment verification'
        )

    def handle(self, *args, **options):
        merchant_id = options['merchant_id']
        is_sandbox = options['sandbox']
        callback_url = options['callback_url']

        # Check if gateway already exists
        existing_gateway = PaymentGateway.objects.filter(
            gateway_type='zarinpal'
        ).first()

        if existing_gateway:
            self.stdout.write(
                self.style.WARNING('ZarinPal gateway already exists. Updating...')
            )
            gateway = existing_gateway
        else:
            self.stdout.write('Creating ZarinPal payment gateway...')
            gateway = PaymentGateway()

        # Set gateway properties
        gateway.name = 'ZarinPal (Sandbox)' if is_sandbox else 'ZarinPal'
        gateway.gateway_type = 'zarinpal'
        gateway.merchant_id = merchant_id
        gateway.is_sandbox = is_sandbox
        gateway.callback_url = callback_url
        gateway.is_active = True

        # Set API URLs based on environment
        if is_sandbox:
            gateway.zp_api_request = 'https://sandbox.zarinpal.com/pg/v4/payment/request.json'
            gateway.zp_api_verify = 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json'
            gateway.zp_api_startpay = 'https://sandbox.zarinpal.com/pg/StartPay/{authority}'
        else:
            gateway.zp_api_request = 'https://payment.zarinpal.com/pg/v4/payment/request.json'
            gateway.zp_api_verify = 'https://payment.zarinpal.com/pg/v4/payment/verify.json'
            gateway.zp_api_startpay = 'https://payment.zarinpal.com/pg/StartPay/{authority}'

        gateway.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully {"updated" if existing_gateway else "created"} '
                f'ZarinPal gateway (ID: {gateway.id})'
            )
        )
        
        self.stdout.write(f'Merchant ID: {gateway.merchant_id}')
        self.stdout.write(f'Environment: {"Sandbox" if is_sandbox else "Production"}')
        self.stdout.write(f'Callback URL: {gateway.callback_url}')
        self.stdout.write(f'Status: {"Active" if gateway.is_active else "Inactive"}') 