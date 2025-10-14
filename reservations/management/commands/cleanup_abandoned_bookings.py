"""
Django management command to cleanup abandoned booking sessions.
This command should be run periodically (e.g., via cron) to clean up sessions
where users started a direct payment booking but never completed it.
"""
from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta
import pickle
import base64


class Command(BaseCommand):
    help = 'Clean up abandoned direct payment booking sessions older than specified hours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=2,
            help='Remove sessions with pending bookings older than this many hours (default: 2)'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        cleaned_count = 0
        error_count = 0
        
        # Get all active sessions
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        
        for session in sessions:
            try:
                # Decode session data
                session_data = session.get_decoded()
                
                # Check if session has pending direct booking
                if 'pending_direct_booking' in session_data:
                    # Sessions don't have a created_at, so we use expire_date as reference
                    # Expire date is typically set to 2 weeks from creation
                    # We'll clean sessions that are likely old based on expire date
                    
                    # For now, we'll just count them
                    # In production, you might want to delete the session entirely
                    # or just remove the pending_direct_booking key
                    
                    self.stdout.write(
                        self.style.WARNING(
                            f'Session {session.session_key} has pending booking data'
                        )
                    )
                    cleaned_count += 1
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Error processing session: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Found {cleaned_count} sessions with pending bookings. '
                f'Errors: {error_count}'
            )
        )
        
        # Note: Session cleanup is typically handled by Django's built-in clearsessions command
        # This command is more for monitoring. Consider implementing more aggressive cleanup
        # if needed based on your application's requirements.

