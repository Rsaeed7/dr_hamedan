from django.core.management.base import BaseCommand
from reservations.models import Reservation
from django.db import transaction


class Command(BaseCommand):
    help = 'Fix reservation amounts that are incorrect by setting them to doctor consultation fee'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all reservations
        reservations = Reservation.objects.select_related('doctor').all()
        
        fixed_count = 0
        total_count = reservations.count()
        
        self.stdout.write(f"Checking {total_count} reservations...")
        
        for reservation in reservations:
            correct_amount = reservation.doctor.consultation_fee
            
            if reservation.amount != correct_amount:
                if dry_run:
                    self.stdout.write(
                        f"Would fix: Reservation {reservation.id} - "
                        f"Current: {reservation.amount}, "
                        f"Correct: {correct_amount}, "
                        f"Doctor: {reservation.doctor}"
                    )
                else:
                    with transaction.atomic():
                        reservation.amount = correct_amount
                        reservation.save()
                        self.stdout.write(
                            f"Fixed: Reservation {reservation.id} - "
                            f"Changed from {reservation.amount} to {correct_amount} "
                            f"for doctor {reservation.doctor}"
                        )
                fixed_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Dry run complete. Would fix {fixed_count} out of {total_count} reservations."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Fixed {fixed_count} out of {total_count} reservations."
                )
            ) 