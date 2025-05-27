from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import time
from doctors.models import Doctor, DoctorAvailability
from doctors.turn_maker import create_availability_days_for_day_of_week


class Command(BaseCommand):
    help = 'Create availability days for all doctor availabilities throughout the Jalali year'

    def add_arguments(self, parser):
        parser.add_argument(
            '--doctor-id',
            type=int,
            help='Create availability days for a specific doctor (optional)',
        )
        parser.add_argument(
            '--day-of-week',
            type=int,
            choices=range(7),
            help='Create availability days for a specific day of week (0=Saturday, 6=Friday)',
        )

    def handle(self, *args, **options):
        doctor_id = options.get('doctor_id')
        day_of_week = options.get('day_of_week')
        
        # Get doctors to process
        if doctor_id:
            try:
                doctors = [Doctor.objects.get(id=doctor_id)]
                self.stdout.write(f"Processing doctor: {doctors[0]}")
            except Doctor.DoesNotExist:
                raise CommandError(f"Doctor with ID {doctor_id} does not exist")
        else:
            doctors = Doctor.objects.all()
            self.stdout.write(f"Processing all {doctors.count()} doctors")
        
        total_days_created = 0
        total_days_updated = 0
        
        for doctor in doctors:
            self.stdout.write(f"\nProcessing doctor: {doctor.user.get_full_name()}")
            
            # Get doctor's availabilities
            availabilities = doctor.availabilities.all()
            if day_of_week is not None:
                availabilities = availabilities.filter(day_of_week=day_of_week)
            
            if not availabilities.exists():
                self.stdout.write(f"  No availabilities found for this doctor")
                continue
                
            for availability in availabilities:
                self.stdout.write(
                    f"  Creating availability days for {availability.get_day_of_week_display()} "
                    f"({availability.start_time} - {availability.end_time})"
                )
                
                try:
                    # Create availability days for this availability
                    result = create_availability_days_for_day_of_week(
                        doctor,
                        availability.day_of_week,
                        availability.start_time,
                        availability.end_time
                    )
                    
                    total_days_created += result['days_created']
                    total_days_updated += result['days_updated']
                    
                    self.stdout.write(
                        f"    Days created: {result['days_created']}"
                    )
                    self.stdout.write(
                        f"    Days updated: {result['days_updated']}"
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"    Error: {str(e)}")
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted! Total days created: {total_days_created}, "
                f"Total days updated: {total_days_updated}"
            )
        ) 