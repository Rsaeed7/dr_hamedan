#!/bin/bash
# Script to create superuser on the server
# Run this when SSH access is available

cd /home/dr_turn_project
source env/bin/activate
export DJANGO_SETTINGS_MODULE=dr_turn.settings_local

echo "Creating superuser with phone: 09397387609"

# Create superuser using Django shell
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

phone = '09397387609'
password = 'Siavash5847'

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
    user = User.objects.create_superuser(
        phone=phone,
        password=password,
        first_name='Siavash',
        last_name='Admin',
        email='siavash@drhmd.ir'
    )
    print(f"Created new superuser: {phone}")

print("Superuser creation completed!")
EOF
