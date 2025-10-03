#!/bin/bash
cd /home/dr_turn_project
source env/bin/activate
export DJANGO_SETTINGS_MODULE=dr_turn.settings_local
python manage.py create_sample_data
echo "Sample data creation completed!"
