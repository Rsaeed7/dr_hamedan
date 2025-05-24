from django.core.management.base import BaseCommand
from django.utils import timezone
from sms_reminders.services import process_pending_reminders, retry_failed_reminders


class Command(BaseCommand):
    help = 'Process pending SMS reminders and retry failed ones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--retry-failed',
            action='store_true',
            help='Also retry failed reminders',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually sending SMS',
        )

    def handle(self, *args, **options):
        start_time = timezone.now()
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting SMS reminder processing at {start_time}')
        )
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No SMS will be sent')
            )
            return
        
        try:
            # Process pending reminders
            self.stdout.write('Processing pending reminders...')
            pending_stats = process_pending_reminders()
            
            self.stdout.write(
                f"Pending reminders processed: "
                f"Sent: {pending_stats['sent']}, "
                f"Failed: {pending_stats['failed']}, "
                f"Skipped: {pending_stats['skipped']}"
            )
            
            # Retry failed reminders if requested
            if options['retry_failed']:
                self.stdout.write('Retrying failed reminders...')
                retry_stats = retry_failed_reminders()
                
                self.stdout.write(
                    f"Failed reminders retried: "
                    f"Retried: {retry_stats['retried']}, "
                    f"Sent: {retry_stats['sent']}, "
                    f"Failed: {retry_stats['failed']}"
                )
            
            # Calculate total processing time
            end_time = timezone.now()
            processing_time = end_time - start_time
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'SMS reminder processing completed in {processing_time.total_seconds():.2f} seconds'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error processing SMS reminders: {str(e)}')
            )
            raise 