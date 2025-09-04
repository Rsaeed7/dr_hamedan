#!/usr/bin/env python
"""
Script to create superuser with specific credentials
Run this when SSH access is available
"""

import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dr_turn.settings_local')
django.setup()

from django.contrib.auth import get_user_model

def create_superuser():
    User = get_user_model()
    
    phone = '09397387609'
    password = 'Siavash5847'
    
    # Check if user already exists
    if User.objects.filter(phone=phone).exists():
        print(f"User with phone {phone} already exists!")
        user = User.objects.get(phone=phone)
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.is_admin = True
        user.save()
        print(f"Updated existing user {phone} to superuser")
    else:
        # Create new superuser
        user = User.objects.create_superuser(
            phone=phone,
            password=password,
            first_name='Siavash',
            last_name='Admin',
            email='siavash@drhmd.ir'
        )
        print(f"Created new superuser: {phone}")
    
    return user

if __name__ == "__main__":
    try:
        user = create_superuser()
        print("Success! Superuser created/updated successfully.")
        print(f"Phone: {user.phone}")
        print(f"Email: {user.email}")
        print(f"Is superuser: {user.is_superuser}")
    except Exception as e:
        print(f"Error: {e}")
