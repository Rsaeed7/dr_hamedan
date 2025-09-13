#!/usr/bin/env python
"""
Web-based sample data creation script
Copy this code and run it in Django shell via admin interface
"""

# Run this in Django shell: http://62.60.198.172/admin/
# Go to Admin -> Shell (if available) or create a management command

import random
import jdatetime
from datetime import datetime, timedelta
from django.contrib.auth.hashers import make_password

# Import models
from user.models import User
from doctors.models import City, Specialization, Doctor, Supplementary_insurance
from patients.models import PatientsFile
from clinics.models import Clinic

def create_sample_data():
    print("Creating sample data...")
    
    # Create cities
    cities_data = ['تهران', 'مشهد', 'اصفهان', 'شیراز', 'تبریز', 'همدان']
    for city_name in cities_data:
        City.objects.get_or_create(name=city_name)
    print(f"Created {len(cities_data)} cities")
    
    # Create specializations
    specializations_data = [
        {'name': 'داخلی', 'description': 'تخصص در بیماری‌های داخلی'},
        {'name': 'قلب و عروق', 'description': 'تخصص در بیماری‌های قلبی'},
        {'name': 'مغز و اعصاب', 'description': 'تخصص در بیماری‌های عصبی'},
        {'name': 'ارتوپدی', 'description': 'تخصص در بیماری‌های استخوان'},
        {'name': 'چشم پزشکی', 'description': 'تخصص در بیماری‌های چشم'},
    ]
    
    for spec_data in specializations_data:
        Specialization.objects.get_or_create(
            name=spec_data['name'],
            defaults={'description': spec_data['description']}
        )
    print(f"Created {len(specializations_data)} specializations")
    
    # Create insurance
    insurances = ['ایران', 'دانا', 'پارسیان', 'سامان', 'تامین اجتماعی']
    for insurance_name in insurances:
        Supplementary_insurance.objects.get_or_create(name=insurance_name)
    print(f"Created {len(insurances)} insurances")
    
    # Create doctor users
    doctor_names = [
        ('دکتر', 'احمدی'), ('دکتر', 'محمدی'), ('دکتر', 'رضایی'),
        ('دکتر', 'حسینی'), ('دکتر', 'کریمی')
    ]
    
    cities = list(City.objects.all())
    specializations = list(Specialization.objects.all())
    insurances = list(Supplementary_insurance.objects.all())
    
    for i, (title, last_name) in enumerate(doctor_names):
        # Create user
        user, created = User.objects.get_or_create(
            phone=f'0912000000{i+1}',
            defaults={
                'first_name': title,
                'last_name': last_name,
                'email': f'doctor{i+1}@drhmd.ir',
                'password': make_password('doctor123')
            }
        )
        
        # Create doctor
        doctor, created = Doctor.objects.get_or_create(
            user=user,
            defaults={
                'specialization': random.choice(specializations),
                'license_number': f'DR{i+1:04d}',
                'city': random.choice(cities),
                'bio': f'دکتر {last_name} با بیش از {random.randint(5, 20)} سال سابقه',
                'consultation_fee': random.randint(100000, 500000),
                'consultation_duration': 30,
                'is_independent': True,
                'is_available': True,
                'address': f'همدان، خیابان بوعلی، پلاک {random.randint(1, 100)}',
                'phone': user.phone,
                'gender': random.choice(['male', 'female']),
                'online_visit': True,
                'online_visit_fee': random.randint(80000, 300000),
                'national_id': f'{random.randint(1000000000, 9999999999)}'
            }
        )
        
        # Add insurance
        doctor.Insurance.set(random.sample(insurances, random.randint(1, 3)))
    
    print(f"Created {len(doctor_names)} doctors")
    print("Sample data creation completed!")
    
    # Print summary
    print(f"Total users: {User.objects.count()}")
    print(f"Total doctors: {Doctor.objects.count()}")
    print(f"Total cities: {City.objects.count()}")
    print(f"Total specializations: {Specialization.objects.count()}")

# Run the function
if __name__ == "__main__":
    create_sample_data()
