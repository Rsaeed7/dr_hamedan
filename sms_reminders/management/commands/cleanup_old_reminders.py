from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from sms_reminders.models import SMSReminder


class Command(BaseCommand):
    help = 'Clean up old SMS reminders to maintain database performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete reminders older than this many days (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--keep-failed',
            action='store_true',
            help='Keep failed reminders for analysis',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        keep_failed = options['keep_failed']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(
            f'Cleaning up SMS reminders older than {days} days '
            f'(before {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")})'
        )
        
        # Build query
        query = SMSReminder.objects.filter(created_at__lt=cutoff_date)
        
        if keep_failed:
            query = query.exclude(status='failed')
            self.stdout.write('Keeping failed reminders for analysis')
        
        # Get counts by status
        total_count = query.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS('No old reminders found to clean up')
            )
            return
        
        # Show breakdown by status
        status_breakdown = {}
        for status_choice in SMSReminder.STATUS_CHOICES:
            status = status_choice[0]
            count = query.filter(status=status).count()
            if count > 0:
                status_breakdown[status] = count
        
        self.stdout.write(f'Found {total_count} reminders to clean up:')
        for status, count in status_breakdown.items():
            self.stdout.write(f'  - {status}: {count}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    'DRY RUN MODE - No reminders will be deleted'
                )
            )
            return
        
        # Confirm deletion for large numbers
        if total_count > 1000:
            confirm = input(
                f'Are you sure you want to delete {total_count} reminders? '
                'Type "yes" to confirm: '
            )
            if confirm.lower() != 'yes':
                self.stdout.write('Operation cancelled')
                return
        
        try:
            # Delete the reminders
            deleted_count, deleted_breakdown = query.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {deleted_count} old SMS reminders'
                )
            )
            
            # Show what was deleted
            if deleted_breakdown:
                self.stdout.write('Deleted breakdown:')
                for model, count in deleted_breakdown.items():
                    if count > 0:
                        self.stdout.write(f'  - {model}: {count}')
                        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error cleaning up reminders: {str(e)}')
            )
            raise 