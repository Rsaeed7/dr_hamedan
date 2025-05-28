from django.core.management.base import BaseCommand
from docpages.models import MedicalLens


class Command(BaseCommand):
    help = 'Populate the database with default medical lenses'

    def handle(self, *args, **options):
        medical_lenses = [
            {
                'name': 'قلب و عروق',
                'description': 'بیماری‌های قلبی و عروقی',
                'color': '#e74c3c'
            },
            {
                'name': 'داخلی',
                'description': 'طب داخلی و بیماری‌های عمومی',
                'color': '#3498db'
            },
            {
                'name': 'جراحی',
                'description': 'جراحی عمومی و تخصصی',
                'color': '#2ecc71'
            },
            {
                'name': 'اطفال',
                'description': 'کودکان و نوزادان',
                'color': '#f39c12'
            },
            {
                'name': 'زنان و زایمان',
                'description': 'زنان، زایمان و مامایی',
                'color': '#e91e63'
            },
            {
                'name': 'روانپزشکی',
                'description': 'سلامت روان و روانپزشکی',
                'color': '#9b59b6'
            },
            {
                'name': 'چشم‌پزشکی',
                'description': 'بیماری‌های چشم',
                'color': '#00bcd4'
            },
            {
                'name': 'گوش و حلق و بینی',
                'description': 'ENT - گوش، حلق و بینی',
                'color': '#ff9800'
            },
            {
                'name': 'ارتوپدی',
                'description': 'استخوان و مفاصل',
                'color': '#795548'
            },
            {
                'name': 'پوست',
                'description': 'پوست و مو',
                'color': '#ff5722'
            },
            {
                'name': 'نورولوژی',
                'description': 'اعصاب و مغز',
                'color': '#607d8b'
            },
            {
                'name': 'رادیولوژی',
                'description': 'تصویربرداری پزشکی',
                'color': '#9e9e9e'
            },
            {
                'name': 'طب اورژانس',
                'description': 'اورژانس و فوریت‌های پزشکی',
                'color': '#f44336'
            },
            {
                'name': 'تغذیه',
                'description': 'تغذیه و رژیم درمانی',
                'color': '#4caf50'
            },
            {
                'name': 'فیزیوتراپی',
                'description': 'فیزیوتراپی و توانبخشی',
                'color': '#03a9f4'
            },
            {
                'name': 'دندانپزشکی',
                'description': 'دندان و دهان',
                'color': '#00e676'
            },
            {
                'name': 'طب سنتی',
                'description': 'طب سنتی و طبیعی',
                'color': '#8bc34a'
            },
            {
                'name': 'سلامت عمومی',
                'description': 'نکات سلامتی و پیشگیری',
                'color': '#009688'
            },
            {
                'name': 'آزمایشگاه',
                'description': 'آزمایشات و تشخیص طبی',
                'color': '#673ab7'
            },
            {
                'name': 'اپیدمیولوژی',
                'description': 'بیماری‌های واگیر و همه‌گیری',
                'color': '#ff1744'
            }
        ]

        created_count = 0
        updated_count = 0

        for lens_data in medical_lenses:
            lens, created = MedicalLens.objects.get_or_create(
                name=lens_data['name'],
                defaults={
                    'description': lens_data['description'],
                    'color': lens_data['color']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created medical lens: {lens.name}')
                )
            else:
                # Update existing lens
                lens.description = lens_data['description']
                lens.color = lens_data['color']
                lens.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated medical lens: {lens.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully populated medical lenses!\n'
                f'Created: {created_count}\n'
                f'Updated: {updated_count}\n'
                f'Total: {created_count + updated_count}'
            )
        ) 