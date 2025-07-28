from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PaymentRequest, PaymentLog


@receiver(post_save, sender=PaymentRequest)
def payment_request_post_save(sender, instance, created, **kwargs):
    """سیگنال پس از ذخیره درخواست پرداخت"""
    if created:
        # ثبت لاگ ایجاد درخواست پرداخت
        PaymentLog.objects.create(
            payment_request=instance,
            log_type='request',
            message=f'درخواست پرداخت جدید ایجاد شد - مبلغ: {instance.amount} تومان',
            data={
                'amount': float(instance.amount),
                'gateway': instance.gateway.name,
                'user_id': instance.user.id
            }
        )
    else:
        # ثبت لاگ وضعیت فعلی (بدون tracking تغییرات)
        PaymentLog.objects.create(
            payment_request=instance,
            log_type='request',
            message=f'وضعیت پرداخت: {instance.status} - مبلغ: {instance.amount} تومان',
            data={
                'status': instance.status,
                'amount': float(instance.amount),
                'gateway': instance.gateway.name
            }
        ) 