from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta, datetime
from sms_reminders.models import SMSReminder, SMSReminderSettings
import json


class Command(BaseCommand):
    help = 'Generate SMS reminder usage and performance reports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Generate report for the last N days (default: 7)',
        )
        parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format (default: text)',
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Include detailed breakdown by reminder type',
        )

    def handle(self, *args, **options):
        days = options['days']
        output_format = options['format']
        detailed = options['detailed']
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get basic statistics
        total_reminders = SMSReminder.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        stats = {
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d %H:%M:%S'),
                'end_date': end_date.strftime('%Y-%m-%d %H:%M:%S'),
                'days': days
            },
            'total_reminders': total_reminders.count(),
            'status_breakdown': {},
            'reminder_type_breakdown': {},
            'daily_breakdown': {},
            'success_rate': 0,
            'settings': {}
        }
        
        # Status breakdown
        status_counts = total_reminders.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        for item in status_counts:
            stats['status_breakdown'][item['status']] = item['count']
        
        # Calculate success rate
        sent_count = stats['status_breakdown'].get('sent', 0)
        if stats['total_reminders'] > 0:
            stats['success_rate'] = round(
                (sent_count / stats['total_reminders']) * 100, 2
            )
        
        # Reminder type breakdown
        if detailed:
            type_counts = total_reminders.values('reminder_type').annotate(
                count=Count('id')
            ).order_by('reminder_type')
            
            for item in type_counts:
                stats['reminder_type_breakdown'][item['reminder_type']] = item['count']
        
        # Daily breakdown
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            day_count = total_reminders.filter(
                created_at__gte=day_start,
                created_at__lt=day_end
            ).count()
            
            day_sent = total_reminders.filter(
                created_at__gte=day_start,
                created_at__lt=day_end,
                status='sent'
            ).count()
            
            stats['daily_breakdown'][day_start.strftime('%Y-%m-%d')] = {
                'total': day_count,
                'sent': day_sent,
                'success_rate': round((day_sent / day_count * 100), 2) if day_count > 0 else 0
            }
        
        # Get current settings
        try:
            settings = SMSReminderSettings.objects.first()
            if settings:
                stats['settings'] = {
                    'reminder_24h_enabled': settings.reminder_24h_enabled,
                    'reminder_2h_enabled': settings.reminder_2h_enabled,
                    'confirmation_sms_enabled': settings.confirmation_sms_enabled,
                    'cancellation_sms_enabled': settings.cancellation_sms_enabled,
                    'working_hour_start': str(settings.working_hour_start),
                    'working_hour_end': str(settings.working_hour_end),
                    'max_retry_attempts': settings.max_retry_attempts,
                    'retry_interval_minutes': settings.retry_interval_minutes
                }
        except Exception:
            stats['settings'] = {'error': 'Could not load settings'}
        
        # Output the report
        if output_format == 'json':
            self.stdout.write(json.dumps(stats, indent=2, ensure_ascii=False))
        else:
            self._print_text_report(stats, detailed)

    def _print_text_report(self, stats, detailed):
        """Print a formatted text report"""
        self.stdout.write(
            self.style.SUCCESS('=== SMS Reminder Report ===')
        )
        
        # Period info
        period = stats['period']
        self.stdout.write(f"Period: {period['start_date']} to {period['end_date']} ({period['days']} days)")
        self.stdout.write('')
        
        # Summary
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(f"Total Reminders: {stats['total_reminders']}")
        self.stdout.write(f"Success Rate: {stats['success_rate']}%")
        self.stdout.write('')
        
        # Status breakdown
        self.stdout.write(self.style.SUCCESS('Status Breakdown:'))
        for status, count in stats['status_breakdown'].items():
            percentage = round((count / stats['total_reminders'] * 100), 2) if stats['total_reminders'] > 0 else 0
            self.stdout.write(f"  {status.title()}: {count} ({percentage}%)")
        self.stdout.write('')
        
        # Reminder type breakdown (if detailed)
        if detailed and stats['reminder_type_breakdown']:
            self.stdout.write(self.style.SUCCESS('Reminder Type Breakdown:'))
            for reminder_type, count in stats['reminder_type_breakdown'].items():
                percentage = round((count / stats['total_reminders'] * 100), 2) if stats['total_reminders'] > 0 else 0
                self.stdout.write(f"  {reminder_type.title()}: {count} ({percentage}%)")
            self.stdout.write('')
        
        # Daily breakdown
        self.stdout.write(self.style.SUCCESS('Daily Breakdown:'))
        for date, data in stats['daily_breakdown'].items():
            self.stdout.write(
                f"  {date}: {data['total']} total, {data['sent']} sent ({data['success_rate']}%)"
            )
        self.stdout.write('')
        
        # Settings
        if 'error' not in stats['settings']:
            self.stdout.write(self.style.SUCCESS('Current Settings:'))
            settings = stats['settings']
            self.stdout.write(f"  24h Reminders: {settings['reminder_24h_enabled']}")
            self.stdout.write(f"  2h Reminders: {settings['reminder_2h_enabled']}")
            self.stdout.write(f"  Confirmations: {settings['confirmation_sms_enabled']}")
            self.stdout.write(f"  Cancellations: {settings['cancellation_sms_enabled']}")
            self.stdout.write(f"  Working Hours: {settings['working_hour_start']} - {settings['working_hour_end']}")
            self.stdout.write(f"  Max Retry Attempts: {settings['max_retry_attempts']}")
            self.stdout.write(f"  Retry Interval: {settings['retry_interval_minutes']} minutes")
        else:
            self.stdout.write(
                self.style.ERROR(f"Settings Error: {stats['settings']['error']}")
            ) 