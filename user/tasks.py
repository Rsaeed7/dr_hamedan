from celery import shared_task
from .models import Otp  # مدل ذخیره OTP

@shared_task
def delete_expired_otp(otp_id):
    Otp.objects.filter(id=otp_id).delete()