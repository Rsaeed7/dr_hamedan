from django.core.management.base import BaseCommand, CommandError
from utils.sms_service import sms_service


class Command(BaseCommand):
    help = 'Send a test SMS to verify SMS functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            'phone_number',
            type=str,
            help='Phone number to send test SMS to (format: 09384104825)',
        )
        parser.add_argument(
            '--message',
            type=str,
            default='این یک پیام تست از سیستم یادآوری پیامک دکتر ترن است.',
            help='Custom test message to send',
        )

    def handle(self, *args, **options):
        phone_number = options['phone_number']
        message = options['message']
        
        # Validate phone number format
        if not phone_number.startswith('09') or len(phone_number) != 11:
            raise CommandError(
                'Invalid phone number format. Use format: 09384104825'
            )
        
        self.stdout.write(f'Sending test SMS to {phone_number}...')
        self.stdout.write(f'Message: {message}')
        
        try:
            result = sms_service.send_sms(phone_number, message)
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Test SMS sent successfully to {phone_number}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to send test SMS to {phone_number}: {result["message"]}'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error sending test SMS: {str(e)}')
            )
            raise 