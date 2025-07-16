#!/usr/bin/env python
"""
Django Management Command to create sample data for all models
Usage: python manage.py create_sample_data
"""

import random
import jdatetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.hashers import make_password

# Import all models
from user.models import User
from doctors.models import (
    City, Specialization, Doctor, DrComment, DoctorAvailability, 
    DoctorBlockedDay, Email, EmailTemplate, DoctorRegistration,
    Notification, Supplementary_insurance, CommentTips, DrServices
)
from patients.models import PatientsFile
from clinics.models import Clinic, ClinicSpecialty, ClinicGallery, ClinicComment
from reservations.models import ReservationDay, Reservation
from wallet.models import Wallet, Transaction, PaymentGateway
from chatmed.models import ChatRequest, ChatRoom, Message, DoctorAvailability as ChatDoctorAvailability
from docpages.models import MedicalLens, Post
from medimag.models import Category, Article
from homecare.models import ServiceCategory, Service, HomeCareRequest
from discounts.models import (
    DiscountType, Discount, CouponCode, DiscountUsage, 
    AutomaticDiscount, DiscountReport
)
from sms_reminders.models import (
    SMSReminder, SMSReminderTemplate, SMSReminderSettings, SMSLog
)
from support.models import SupportChatRoom, SupportMessage, Contact, ContactUs
from about_us.models import AboutUs, FAQ, TeamMember


class Command(BaseCommand):
    help = 'Create sample data for all models in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new sample data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()
        
        self.stdout.write('Creating sample data...')
        
        with transaction.atomic():
            self.create_cities()
            self.create_specializations()
            self.create_supplementary_insurances()
            self.create_users()
            self.create_clinics()
            self.create_doctors()
            self.create_patients()
            self.create_wallets()
            self.create_reservation_days()
            self.create_reservations()
            self.create_chat_requests()
            self.create_messages()
            self.create_posts()
            self.create_articles()
            self.create_homecare_services()
            self.create_discounts()
            self.create_sms_reminders()
            self.create_support_chats()
            self.create_about_us_data()
            
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )

    def clear_data(self):
        """Clear all existing data"""
        models_to_clear = [
            Message, ChatRoom, ChatRequest, ChatDoctorAvailability,
            Reservation, ReservationDay, DrComment, DoctorAvailability,
            DoctorBlockedDay, Email, EmailTemplate, DoctorRegistration,
            Notification, DrServices, ClinicComment, ClinicGallery,
            ClinicSpecialty, Clinic, Doctor, PatientsFile, User,
            Transaction, Wallet, PaymentGateway, Post, MedicalLens,
            Article, Category, HomeCareRequest, Service, ServiceCategory,
            DiscountUsage, CouponCode, Discount, DiscountType,
            AutomaticDiscount, DiscountReport, SMSLog, SMSReminder,
            SMSReminderTemplate, SMSReminderSettings, SupportMessage,
            SupportChatRoom, ContactUs, Contact, AboutUs, FAQ, TeamMember,
            City, Specialization, Supplementary_insurance
        ]
        
        for model in models_to_clear:
            model.objects.all().delete()

    def create_cities(self):
        """Create sample cities"""
        cities_data = [
            'تهران', 'مشهد', 'اصفهان', 'شیراز', 'تبریز', 'قم', 'اهواز', 'کرج',
            'کرمانشاه', 'ارومیه', 'یزد', 'قم', 'قم', 'قم', 'قم'
        ]
        
        for city_name in cities_data:
            City.objects.get_or_create(name=city_name)
        
        self.stdout.write(f'Created {len(cities_data)} cities')

    def create_specializations(self):
        """Create sample specializations"""
        specializations_data = [
            {'name': 'داخلی', 'description': 'تخصص در بیماری‌های داخلی'},
            {'name': 'قلب و عروق', 'description': 'تخصص در بیماری‌های قلبی'},
            {'name': 'مغز و اعصاب', 'description': 'تخصص در بیماری‌های عصبی'},
            {'name': 'ارتوپدی', 'description': 'تخصص در بیماری‌های استخوان و مفاصل'},
            {'name': 'چشم پزشکی', 'description': 'تخصص در بیماری‌های چشم'},
            {'name': 'پوست و مو', 'description': 'تخصص در بیماری‌های پوستی'},
            {'name': 'گوارش', 'description': 'تخصص در بیماری‌های گوارشی'},
            {'name': 'روانپزشکی', 'description': 'تخصص در بیماری‌های روانی'},
            {'name': 'زنان و زایمان', 'description': 'تخصص در بیماری‌های زنان'},
            {'name': 'کودکان', 'description': 'تخصص در بیماری‌های کودکان'},
        ]
        
        for spec_data in specializations_data:
            Specialization.objects.get_or_create(
                name=spec_data['name'],
                defaults={'description': spec_data['description']}
            )
        
        self.stdout.write(f'Created {len(specializations_data)} specializations')

    def create_supplementary_insurances(self):
        """Create sample supplementary insurances"""
        insurances = [
            'ایران', 'دانا', 'پارسیان', 'سامان', 'سینا', 'تامین اجتماعی',
            'خدمات درمانی', 'نیروهای مسلح', 'بیمه سلامت'
        ]
        
        for insurance_name in insurances:
            Supplementary_insurance.objects.get_or_create(name=insurance_name)
        
        self.stdout.write(f'Created {len(insurances)} supplementary insurances')

    def create_users(self):
        """Create sample users (doctors and patients)"""
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            phone='09123456789',
            defaults={
                'first_name': 'مدیر',
                'last_name': 'سیستم',
                'email': 'admin@drturn.ir',
                'is_admin': True,
                'is_staff': True,
                'is_superuser': True,
                'password': make_password('admin123')
            }
        )
        
        # Create doctor users
        doctor_names = [
            ('دکتر', 'احمدی', 'متخصص داخلی'),
            ('دکتر', 'محمدی', 'متخصص قلب'),
            ('دکتر', 'رضایی', 'متخصص مغز و اعصاب'),
            ('دکتر', 'حسینی', 'متخصص ارتوپدی'),
            ('دکتر', 'کریمی', 'متخصص چشم'),
            ('دکتر', 'جعفری', 'متخصص پوست'),
            ('دکتر', 'مهدوی', 'متخصص گوارش'),
            ('دکتر', 'نوری', 'روانپزشک'),
            ('دکتر', 'صادقی', 'متخصص زنان'),
            ('دکتر', 'فرهادی', 'متخصص کودکان'),
        ]
        
        doctor_users = []
        for i, (title, last_name, specialty) in enumerate(doctor_names):
            user, created = User.objects.get_or_create(
                phone=f'0912000000{i+1}',
                defaults={
                    'first_name': title,
                    'last_name': last_name,
                    'email': f'doctor{i+1}@drturn.ir',
                    'password': make_password('doctor123')
                }
            )
            doctor_users.append(user)
        
        # Create patient users
        patient_names = [
            ('علی', 'احمدی'),
            ('فاطمه', 'محمدی'),
            ('حسن', 'رضایی'),
            ('زهرا', 'حسینی'),
            ('محمد', 'کریمی'),
            ('مریم', 'جعفری'),
            ('حسین', 'مهدوی'),
            ('نرگس', 'نوری'),
            ('امیر', 'صادقی'),
            ('سارا', 'فرهادی'),
        ]
        
        patient_users = []
        for i, (first_name, last_name) in enumerate(patient_names):
            user, created = User.objects.get_or_create(
                phone=f'0913000000{i+1}',
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': f'patient{i+1}@drturn.ir',
                    'password': make_password('patient123')
                }
            )
            patient_users.append(user)
        
        self.doctor_users = doctor_users
        self.patient_users = patient_users
        self.admin_user = admin_user
        
        self.stdout.write(f'Created {len(doctor_users)} doctor users and {len(patient_users)} patient users')

    def create_clinics(self):
        """Create sample clinics"""
        clinics_data = [
            {
                'name': 'کلینیک سلامت',
                'address': 'تهران، خیابان ولیعصر، پلاک 123',
                'phone': '021-12345678',
                'email': 'info@salamat-clinic.ir',
                'description': 'کلینیک تخصصی سلامت با ارائه خدمات پزشکی با کیفیت'
            },
            {
                'name': 'مرکز درمانی امید',
                'address': 'مشهد، خیابان امام رضا، پلاک 456',
                'phone': '051-87654321',
                'email': 'info@omid-medical.ir',
                'description': 'مرکز درمانی امید با بیش از 20 سال سابقه'
            },
            {
                'name': 'کلینیک تخصصی آرامش',
                'address': 'اصفهان، خیابان چهارباغ، پلاک 789',
                'phone': '031-11223344',
                'email': 'info@aramsh-clinic.ir',
                'description': 'کلینیک تخصصی آرامش با محیطی آرام و حرفه‌ای'
            }
        ]
        
        self.clinics = []
        for clinic_data in clinics_data:
            clinic, created = Clinic.objects.get_or_create(
                name=clinic_data['name'],
                defaults={
                    'address': clinic_data['address'],
                    'phone': clinic_data['phone'],
                    'email': clinic_data['email'],
                    'description': clinic_data['description'],
                    'admin': self.admin_user
                }
            )
            self.clinics.append(clinic)
        
        self.stdout.write(f'Created {len(self.clinics)} clinics')

    def create_doctors(self):
        """Create sample doctors"""
        cities = list(City.objects.all())
        specializations = list(Specialization.objects.all())
        insurances = list(Supplementary_insurance.objects.all())
        
        self.doctors = []
        for i, user in enumerate(self.doctor_users):
            doctor, created = Doctor.objects.get_or_create(
                user=user,
                defaults={
                    'specialization': random.choice(specializations),
                    'license_number': f'DR{i+1:04d}',
                    'city': random.choice(cities),
                    'bio': f'دکتر {user.last_name} با بیش از {random.randint(5, 20)} سال سابقه در زمینه {user.last_name}',
                    'consultation_fee': Decimal(random.randint(100000, 500000)),
                    'consultation_duration': random.choice([30, 45, 60]),
                    'is_independent': random.choice([True, False]),
                    'is_available': True,
                    'clinic': random.choice(self.clinics) if not random.choice([True, False]) else None,
                    'address': f'تهران، خیابان {random.choice(["ولیعصر", "انقلاب", "شریعتی"])}، پلاک {random.randint(1, 100)}',
                    'phone': user.phone,
                    'gender': random.choice(['male', 'female']),
                    'online_visit': True,
                    'online_visit_fee': Decimal(random.randint(80000, 300000)),
                    'national_id': f'{random.randint(1000000000, 9999999999)}'
                }
            )
            
            # Add insurance
            doctor.Insurance.set(random.sample(insurances, random.randint(1, 3)))
            
            # Create availability
            for day in range(7):
                if random.choice([True, False]):  # 50% chance of being available
                    DoctorAvailability.objects.get_or_create(
                        doctor=doctor,
                        day_of_week=day,
                        defaults={
                            'start_time': '09:00',
                            'end_time': '17:00'
                        }
                    )
            
            self.doctors.append(doctor)
        
        self.stdout.write(f'Created {len(self.doctors)} doctors')

    def create_patients(self):
        """Create sample patients"""
        cities = list(City.objects.all())
        
        self.patients = []
        for i, user in enumerate(self.patient_users):
            patient, created = PatientsFile.objects.get_or_create(
                user=user,
                defaults={
                    'phone': user.phone,
                    'national_id': f'{random.randint(1000000000, 9999999999)}',
                    'medical_history': f'سابقه پزشکی بیمار {user.get_full_name()}',
                    'birthdate': jdatetime.date.today() - jdatetime.timedelta(days=random.randint(6570, 25550)),  # 18-70 years
                    'gender': random.choice(['male', 'female']),
                    'city': random.choice(cities),
                    'email': user.email
                }
            )
            self.patients.append(patient)
        
        self.stdout.write(f'Created {len(self.patients)} patients')

    def create_wallets(self):
        """Create sample wallets"""
        self.wallets = []
        for user in self.patient_users + self.doctor_users:
            wallet, created = Wallet.objects.get_or_create(
                user=user,
                defaults={
                    'balance': Decimal(random.randint(0, 1000000)),
                    'pending_balance': Decimal(random.randint(0, 500000)),
                    'frozen_balance': Decimal(0)
                }
            )
            self.wallets.append(wallet)
        
        self.stdout.write(f'Created {len(self.wallets)} wallets')

    def create_reservation_days(self):
        """Create sample reservation days"""
        # Create reservation days for next 30 days
        self.reservation_days = []
        for i in range(30):
            date = jdatetime.date.today() + jdatetime.timedelta(days=i)
            day, created = ReservationDay.objects.get_or_create(
                date=date,
                defaults={'published': True}
            )
            self.reservation_days.append(day)
        
        self.stdout.write(f'Created {len(self.reservation_days)} reservation days')

    def create_reservations(self):
        """Create sample reservations"""
        self.reservations = []
        time_slots = ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', 
                     '14:00', '14:30', '15:00', '15:30', '16:00', '16:30']
        
        for day in self.reservation_days[:10]:  # First 10 days
            for doctor in self.doctors[:5]:  # First 5 doctors
                for time_slot in time_slots[:6]:  # First 6 time slots
                    if random.choice([True, False]):  # 50% chance of being booked
                        patient = random.choice(self.patients)
                        reservation, created = Reservation.objects.get_or_create(
                            day=day,
                            doctor=doctor,
                            time=time_slot,
                            defaults={
                                'patient': patient,
                                'phone': patient.phone,
                                'status': random.choice(['available', 'pending', 'confirmed', 'completed']),
                                'payment_status': random.choice(['pending', 'paid', 'failed']),
                                'amount': doctor.consultation_fee,
                                'patient_name': patient.user.get_full_name(),
                                'notes': f'نوبت {patient.user.get_full_name()} با {doctor.user.get_full_name()}'
                            }
                        )
                        self.reservations.append(reservation)
        
        self.stdout.write(f'Created {len(self.reservations)} reservations')

    def create_chat_requests(self):
        """Create sample chat requests"""
        self.chat_requests = []
        for i in range(20):
            patient = random.choice(self.patients)
            doctor = random.choice(self.doctors)
            
            chat_request, created = ChatRequest.objects.get_or_create(
                patient=patient,
                doctor=doctor,
                defaults={
                    'disease_summary': f'خلاصه بیماری بیمار {patient.user.get_full_name()}',
                    'status': random.choice(['pending', 'approved', 'rejected', 'finished']),
                    'payment_status': random.choice(['pending', 'paid', 'failed']),
                    'amount': doctor.online_visit_fee,
                    'patient_name': patient.user.get_full_name(),
                    'patient_national_id': patient.national_id,
                    'phone': patient.phone
                }
            )
            self.chat_requests.append(chat_request)
        
        self.stdout.write(f'Created {len(self.chat_requests)} chat requests')

    def create_messages(self):
        """Create sample messages"""
        self.messages = []
        for chat_request in self.chat_requests[:10]:  # First 10 chat requests
            if chat_request.status == 'approved':
                # Create chat room
                chat_room, created = ChatRoom.objects.get_or_create(
                    request=chat_request,
                    defaults={'is_active': True}
                )
                
                # Create messages
                for i in range(random.randint(3, 10)):
                    sender = random.choice([chat_request.patient.user, chat_request.doctor.user])
                    message, created = Message.objects.get_or_create(
                        chat_room=chat_room,
                        sender=sender,
                        defaults={
                            'content': f'پیام {i+1} از {sender.get_full_name()}',
                            'message_type': 'text',
                            'is_read': random.choice([True, False])
                        }
                    )
                    self.messages.append(message)
        
        self.stdout.write(f'Created {len(self.messages)} messages')

    def create_posts(self):
        """Create sample posts"""
        medical_lenses = list(MedicalLens.objects.all())
        if not medical_lenses:
            # Create some medical lenses if none exist
            lens_names = ['لنز طبی', 'لنز رنگی', 'لنز آستیگمات', 'لنز چندکاناله']
            for name in lens_names:
                MedicalLens.objects.get_or_create(name=name)
            medical_lenses = list(MedicalLens.objects.all())
        
        self.posts = []
        for i, doctor in enumerate(self.doctors[:5]):  # First 5 doctors
            for j in range(random.randint(1, 3)):  # 1-3 posts per doctor
                post, created = Post.objects.get_or_create(
                    doctor=doctor,
                    title=f'مقاله {j+1} از دکتر {doctor.user.last_name}',
                    defaults={
                        'content': f'محتوی مقاله {j+1} از دکتر {doctor.user.last_name} در زمینه {doctor.specialization.name}',
                        'media_type': random.choice(['none', 'image', 'video']),
                        'status': 'published',
                        'likes_count': random.randint(0, 100)
                    }
                )
                
                # Add medical lenses
                post.medical_lenses.set(random.sample(medical_lenses, random.randint(1, 2)))
                self.posts.append(post)
        
        self.stdout.write(f'Created {len(self.posts)} posts')

    def create_articles(self):
        """Create sample articles"""
        categories = list(Category.objects.all())
        if not categories:
            # Create some categories if none exist
            category_names = ['سلامت عمومی', 'تغذیه', 'ورزش', 'سلامت روان']
            for name in category_names:
                Category.objects.get_or_create(name=name, slug=name.lower().replace(' ', '-'))
            categories = list(Category.objects.all())
        
        self.articles = []
        for i in range(15):
            article, created = Article.objects.get_or_create(
                title=f'مقاله {i+1} در مورد سلامت',
                defaults={
                    'category': random.choice(categories),
                    'content': f'محتوی مقاله {i+1} در مورد سلامت و بهداشت',
                    'summary': f'خلاصه مقاله {i+1}',
                    'author': random.choice(self.doctor_users),
                    'status': 'published',
                    'view_count': random.randint(0, 1000)
                }
            )
            self.articles.append(article)
        
        self.stdout.write(f'Created {len(self.articles)} articles')

    def create_homecare_services(self):
        """Create sample homecare services"""
        cities = list(City.objects.all())
        
        # Create service categories
        categories_data = [
            'پرستاری', 'فیزیوتراپی', 'کاردرمانی', 'گفتاردرمانی', 'تغذیه'
        ]
        
        self.service_categories = []
        for cat_name in categories_data:
            category, created = ServiceCategory.objects.get_or_create(name=cat_name)
            self.service_categories.append(category)
        
        # Create services
        services_data = [
            'پرستار شبانه‌روزی', 'فیزیوتراپی در منزل', 'کاردرمانی کودکان',
            'گفتاردرمانی', 'مشاوره تغذیه', 'تزریق در منزل'
        ]
        
        self.services = []
        for service_name in services_data:
            service, created = Service.objects.get_or_create(
                name=service_name,
                defaults={
                    'category': random.choice(self.service_categories),
                    'description': f'خدمت {service_name} در منزل',
                    'price': Decimal(random.randint(50000, 300000))
                }
            )
            self.services.append(service)
        
        # Create homecare requests
        self.homecare_requests = []
        for i in range(10):
            patient = random.choice(self.patients)
            service = random.choice(self.services)
            
            request, created = HomeCareRequest.objects.get_or_create(
                patient=patient,
                service=service,
                defaults={
                    'requested_date': jdatetime.date.today() + jdatetime.timedelta(days=random.randint(1, 30)),
                    'requested_time': '10:00',
                    'city': random.choice(cities),
                    'address': f'آدرس بیمار {patient.user.get_full_name()}',
                    'extra_notes': f'توضیحات اضافی برای درخواست {i+1}',
                    'status': random.choice(['pending', 'contacted', 'confirmed', 'rejected'])
                }
            )
            self.homecare_requests.append(request)
        
        self.stdout.write(f'Created {len(self.services)} services and {len(self.homecare_requests)} homecare requests')

    def create_discounts(self):
        """Create sample discounts"""
        # Create discount types
        types_data = [
            {'name': 'درصدی', 'description': 'تخفیف درصدی'},
            {'name': 'مبلغ ثابت', 'description': 'تخفیف مبلغ ثابت'},
            {'name': 'یک به یک', 'description': 'خرید یک، یکی هدیه'}
        ]
        
        self.discount_types = []
        for type_data in types_data:
            discount_type, created = DiscountType.objects.get_or_create(
                name=type_data['name'],
                defaults={'description': type_data['description']}
            )
            self.discount_types.append(discount_type)
        
        # Create discounts
        self.discounts = []
        for i in range(5):
            discount_type = random.choice(self.discount_types)
            
            discount, created = Discount.objects.get_or_create(
                title=f'تخفیف {i+1}',
                defaults={
                    'description': f'توضیحات تخفیف {i+1}',
                    'discount_type': discount_type,
                    'percentage': Decimal(random.randint(10, 50)) if discount_type.name == 'درصدی' else None,
                    'fixed_amount': Decimal(random.randint(50000, 200000)) if discount_type.name == 'مبلغ ثابت' else None,
                    'applicable_to': random.choice(['all', 'doctor', 'specialization', 'clinic']),
                    'min_amount': Decimal(random.randint(100000, 500000)),
                    'max_discount_amount': Decimal(random.randint(100000, 300000)),
                    'start_date': jdatetime.datetime.now(),
                    'end_date': jdatetime.datetime.now() + jdatetime.timedelta(days=30),
                    'usage_limit': random.randint(50, 200),
                    'usage_limit_per_user': random.randint(1, 3),
                    'status': 'active'
                }
            )
            
            # Add doctors and specializations
            if discount.applicable_to == 'doctor':
                discount.doctors.set(random.sample(self.doctors, random.randint(1, 3)))
            elif discount.applicable_to == 'specialization':
                discount.specializations.set(random.sample(list(Specialization.objects.all()), random.randint(1, 2)))
            
            self.discounts.append(discount)
        
        self.stdout.write(f'Created {len(self.discounts)} discounts')

    def create_sms_reminders(self):
        """Create sample SMS reminders"""
        # Create SMS settings
        settings, created = SMSReminderSettings.objects.get_or_create(
            defaults={
                'enabled_types': ['confirmation', 'reminder_24h', 'reminder_2h'],
                'working_hours_start': '08:00',
                'working_hours_end': '20:00',
                'max_retry_attempts': 3,
                'retry_interval_minutes': 30
            }
        )
        
        # Create SMS templates
        templates_data = [
            {
                'name': 'تایید نوبت',
                'template_id': 'confirmation',
                'message': 'نوبت شما برای {date} ساعت {time} تایید شد. دکتر {doctor}'
            },
            {
                'name': 'یادآوری 24 ساعته',
                'template_id': 'reminder_24h',
                'message': 'یادآوری: فردا ساعت {time} نوبت دکتر {doctor} دارید.'
            },
            {
                'name': 'یادآوری 2 ساعته',
                'template_id': 'reminder_2h',
                'message': 'یادآوری: 2 ساعت دیگر نوبت دکتر {doctor} دارید.'
            }
        ]
        
        self.sms_templates = []
        for template_data in templates_data:
            template, created = SMSReminderTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    'template_id': template_data['template_id'],
                    'message': template_data['message'],
                    'is_active': True
                }
            )
            self.sms_templates.append(template)
        
        # Create SMS reminders
        self.sms_reminders = []
        for reservation in self.reservations[:10]:  # First 10 reservations
            if reservation.status in ['confirmed', 'pending']:
                reminder, created = SMSReminder.objects.get_or_create(
                    reservation=reservation,
                    user=reservation.patient.user,
                    defaults={
                        'reminder_type': random.choice(['confirmation', 'reminder_24h', 'reminder_2h']),
                        'phone_number': reservation.phone,
                        'message': f'یادآوری نوبت دکتر {reservation.doctor.user.get_full_name()}',
                        'scheduled_time': jdatetime.datetime.now() + jdatetime.timedelta(hours=random.randint(1, 24)),
                        'status': random.choice(['pending', 'sent', 'failed'])
                    }
                )
                self.sms_reminders.append(reminder)
        
        self.stdout.write(f'Created {len(self.sms_reminders)} SMS reminders')

    def create_support_chats(self):
        """Create sample support chats"""
        self.support_chats = []
        for i in range(5):
            customer = random.choice(self.patient_users)
            
            chat_room, created = SupportChatRoom.objects.get_or_create(
                customer=customer,
                defaults={
                    'admin': self.admin_user,
                    'title': f'پشتیبانی {customer.get_full_name()}',
                    'is_active': True
                }
            )
            
            # Create messages
            for j in range(random.randint(2, 8)):
                sender = random.choice([customer, self.admin_user])
                message, created = SupportMessage.objects.get_or_create(
                    chat_room=chat_room,
                    sender=sender,
                    defaults={
                        'content': f'پیام پشتیبانی {j+1} از {sender.get_full_name()}',
                        'message_type': 'text',
                        'is_read': random.choice([True, False])
                    }
                )
            
            self.support_chats.append(chat_room)
        
        self.stdout.write(f'Created {len(self.support_chats)} support chats')

    def create_about_us_data(self):
        """Create sample about us data"""
        # Create contact info
        contact, created = Contact.objects.get_or_create(
            defaults={
                'phone_number': '021-12345678',
                'email': 'info@drturn.ir',
                'address': 'تهران، خیابان ولیعصر، پلاک 123',
                'whatsapp': '+989123456789',
                'telegram': '@drturn_support',
                'instagram': '@drturn_official',
                'eitaa': '@drturn_support'
            }
        )
        
        # Create about us
        about_us, created = AboutUs.objects.get_or_create(
            defaults={
                'title': 'درباره دکتر تورن',
                'content': 'دکتر تورن پلتفرمی برای رزرو نوبت پزشکی آنلاین است.',
                'mission': 'ارائه خدمات پزشکی با کیفیت و در دسترس',
                'vision': 'تبدیل شدن به برترین پلتفرم سلامت دیجیتال ایران'
            }
        )
        
        # Create FAQs
        faqs_data = [
            {
                'question': 'چگونه می‌توانم نوبت بگیرم؟',
                'answer': 'از طریق سایت یا اپلیکیشن می‌توانید نوبت بگیرید.'
            },
            {
                'question': 'آیا ویزیت آنلاین امکان‌پذیر است؟',
                'answer': 'بله، بسیاری از پزشکان ویزیت آنلاین ارائه می‌دهند.'
            },
            {
                'question': 'چگونه می‌توانم پرداخت کنم؟',
                'answer': 'از طریق کیف پول یا کارت بانکی می‌توانید پرداخت کنید.'
            }
        ]
        
        self.faqs = []
        for faq_data in faqs_data:
            faq, created = FAQ.objects.get_or_create(
                question=faq_data['question'],
                defaults={'answer': faq_data['answer']}
            )
            self.faqs.append(faq)
        
        # Create team members
        team_data = [
            {'name': 'دکتر احمدی', 'position': 'مدیرعامل', 'bio': 'متخصص داخلی با 15 سال سابقه'},
            {'name': 'دکتر محمدی', 'position': 'مدیر فنی', 'bio': 'متخصص فناوری اطلاعات'},
            {'name': 'دکتر رضایی', 'position': 'مدیر پزشکی', 'bio': 'متخصص قلب و عروق'}
        ]
        
        self.team_members = []
        for member_data in team_data:
            member, created = TeamMember.objects.get_or_create(
                name=member_data['name'],
                defaults={
                    'position': member_data['position'],
                    'bio': member_data['bio']
                }
            )
            self.team_members.append(member)
        
        self.stdout.write('Created about us data, contact info, FAQs, and team members') 