# src/celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# تنظیمات پروژه
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dr_turn.settings')

app = Celery('dr_turn')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


# celery -A lou worker --loglevel=info
