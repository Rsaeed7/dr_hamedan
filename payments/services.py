import json
import requests
from decimal import Decimal
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from .models import PaymentGateway, PaymentRequest, PaymentLog


class CurrencyConverter:
    """تبدیل واحد پول بین تومان و ریال"""
    
    @staticmethod
    def toman_to_rial(toman_amount):
        """تبدیل تومان به ریال"""
        return int(toman_amount * 10)
    
    @staticmethod
    def rial_to_toman(rial_amount):
        """تبدیل ریال به تومان"""
        return int(rial_amount / 10)


class ZarinPalPaymentService:
    """سرویس پرداخت زرین‌پال"""
    
    def __init__(self, gateway=None):
        self.gateway = gateway or PaymentGateway.objects.filter(
            gateway_type='zarinpal', 
            is_active=True
        ).first()
        
        if not self.gateway:
            raise ValueError("درگاه پرداخت زرین‌پال فعال یافت نشد")
    
    def create_payment_request(self, user, amount, description, callback_url=None, metadata=None):
        """ایجاد درخواست پرداخت"""
        try:
            # تبدیل تومان به ریال برای ارسال به درگاه پرداخت
            rial_amount = CurrencyConverter.toman_to_rial(amount)
            
            # ایجاد درخواست پرداخت (مبلغ در دیتابیس به تومان ذخیره می‌شود)
            payment_request = PaymentRequest.objects.create(
                user=user,
                amount=amount,  # مبلغ به تومان در دیتابیس
                description=description,
                gateway=self.gateway,
                callback_url=callback_url or self.gateway.callback_url,
                metadata=metadata or {}
            )
            
            # ارسال درخواست به زرین‌پال
            api_urls = self.gateway.get_api_urls()
            request_url = api_urls.get('request')
            
            if not request_url:
                raise ValueError("آدرس API درگاه پرداخت تنظیم نشده است")
            
            # آماده‌سازی داده‌های درخواست (مبلغ به ریال)
            req_data = {
                "merchant_id": self.gateway.merchant_id,
                "amount": rial_amount,  # مبلغ به ریال برای درگاه پرداخت
                "callback_url": payment_request.callback_url,
                "description": description,
                "metadata": {
                    "mobile": user.phone if hasattr(user, 'phone') else "",
                    "email": user.email,
                    "payment_request_id": payment_request.id
                }
            }
            
            # ارسال درخواست
            req_header = {
                "accept": "application/json",
                "content-type": "application/json"
            }
            
            response = requests.post(
                url=request_url,
                data=json.dumps(req_data),
                headers=req_header,
                timeout=30
            )
            
            response_data = response.json()
            
            # ثبت لاگ
            PaymentLog.objects.create(
                payment_request=payment_request,
                log_type='request',
                message=f"درخواست پرداخت به زرین‌پال ارسال شد (مبلغ: {amount} تومان = {rial_amount} ریال)",
                data={
                    'request_data': req_data,
                    'response_data': response_data,
                    'status_code': response.status_code,
                    'toman_amount': amount,
                    'rial_amount': rial_amount
                }
            )
            
            # بررسی پاسخ
            if response.status_code == 200 and response_data.get('data', {}).get('authority'):
                authority = response_data['data']['authority']
                payment_request.authority = authority
                payment_request.status = 'processing'
                payment_request.save()
                
                # آدرس شروع پرداخت
                startpay_url = api_urls.get('startpay').format(authority=authority)
                
                return {
                    'success': True,
                    'authority': authority,
                    'startpay_url': startpay_url,
                    'payment_request': payment_request
                }
            else:
                error_message = response_data.get('errors', {}).get('message', 'خطای نامشخص')
                payment_request.mark_as_failed(error_message)
                
                return {
                    'success': False,
                    'error': f"خطا در اتصال به درگاه پرداخت: {error_message}"
                }
                
        except requests.RequestException as e:
            # خطا در ارتباط با درگاه پرداخت
            if 'payment_request' in locals():
                payment_request.mark_as_failed(f"خطا در ارتباط: {str(e)}")
            
            return {
                'success': False,
                'error': f"خطا در اتصال به درگاه پرداخت: {str(e)}"
            }
        except Exception as e:
            # خطای عمومی
            if 'payment_request' in locals():
                payment_request.mark_as_failed(f"خطای سیستمی: {str(e)}")
            
            return {
                'success': False,
                'error': f"خطا در ایجاد پرداخت: {str(e)}"
            }
    
    def verify_payment(self, authority, amount):
        """تایید پرداخت"""
        try:
            # یافتن درخواست پرداخت
            payment_request = PaymentRequest.objects.get(authority=authority)
            
            if not payment_request.can_be_processed():
                return {
                    'success': False,
                    'error': 'درخواست پرداخت قابل پردازش نیست'
                }
            
            # تبدیل تومان به ریال برای تایید
            rial_amount = CurrencyConverter.toman_to_rial(amount)
            
            # ارسال درخواست تایید
            api_urls = self.gateway.get_api_urls()
            verify_url = api_urls.get('verify')
            
            req_data = {
                "merchant_id": self.gateway.merchant_id,
                "amount": rial_amount,  # مبلغ به ریال برای تایید
                "authority": authority
            }
            
            req_header = {
                "accept": "application/json",
                "content-type": "application/json"
            }
            
            response = requests.post(
                url=verify_url,
                data=json.dumps(req_data),
                headers=req_header,
                timeout=30
            )
            
            response_data = response.json()
            
            # ثبت لاگ
            PaymentLog.objects.create(
                payment_request=payment_request,
                log_type='verify',
                message=f"درخواست تایید پرداخت ارسال شد (مبلغ: {amount} تومان = {rial_amount} ریال)",
                data={
                    'request_data': req_data,
                    'response_data': response_data,
                    'status_code': response.status_code,
                    'toman_amount': amount,
                    'rial_amount': rial_amount
                }
            )
            
            # بررسی پاسخ
            if response.status_code == 200:
                data = response_data.get('data', {})
                code = data.get('code')
                
                if code in [100, 101]:  # پرداخت موفق
                    ref_id = data.get('ref_id')
                    card_pan = data.get('card_pan', '')
                    
                    # تکمیل پرداخت
                    if payment_request.mark_as_completed(ref_id, card_pan):
                        return {
                            'success': True,
                            'ref_id': ref_id,
                            'card_pan': card_pan,
                            'payment_request': payment_request
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'خطا در تکمیل پرداخت'
                        }
                else:
                    error_message = data.get('message', 'پرداخت ناموفق')
                    payment_request.mark_as_failed(error_message)
                    
                    return {
                        'success': False,
                        'error': error_message,
                        'payment_request': payment_request
                    }
            else:
                error_message = response_data.get('errors', {}).get('message', 'خطا در تایید پرداخت')
                payment_request.mark_as_failed(error_message)
                
                return {
                    'success': False,
                    'error': error_message
                }
                
        except PaymentRequest.DoesNotExist:
            return {
                'success': False,
                'error': 'درخواست پرداخت یافت نشد'
            }
        except Exception as e:
            # ثبت لاگ خطا
            if 'payment_request' in locals():
                PaymentLog.objects.create(
                    payment_request=payment_request,
                    log_type='error',
                    message=f"خطا در تایید پرداخت: {str(e)}",
                    data={'error': str(e)}
                )
            
            return {
                'success': False,
                'error': f"خطا در تایید پرداخت: {str(e)}"
            }


class PaymentService:
    """سرویس اصلی پرداخت"""
    
    @staticmethod
    def create_payment(user, amount, description, gateway_type='zarinpal', callback_url=None, metadata=None):
        """ایجاد پرداخت"""
        try:
            # یافتن درگاه پرداخت
            gateway = PaymentGateway.objects.filter(
                gateway_type=gateway_type,
                is_active=True
            ).first()
            
            if not gateway:
                return {
                    'success': False,
                    'error': f'درگاه پرداخت {gateway_type} فعال یافت نشد'
                }
            
            # بررسی محدودیت‌های مبلغ (مبلغ به تومان)
            if amount < gateway.min_amount:
                return {
                    'success': False,
                    'error': f'حداقل مبلغ پرداخت {gateway.min_amount} تومان است'
                }
            
            if amount > gateway.max_amount:
                return {
                    'success': False,
                    'error': f'حداکثر مبلغ پرداخت {gateway.max_amount} تومان است'
                }
            
            # ایجاد پرداخت بر اساس نوع درگاه
            if gateway_type == 'zarinpal':
                service = ZarinPalPaymentService(gateway)
                return service.create_payment_request(user, amount, description, callback_url, metadata)
            else:
                return {
                    'success': False,
                    'error': f'درگاه پرداخت {gateway_type} پشتیبانی نمی‌شود'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'خطا در ایجاد پرداخت: {str(e)}'
            }
    
    @staticmethod
    def verify_payment(authority, amount, gateway_type='zarinpal'):
        """تایید پرداخت"""
        try:
            if gateway_type == 'zarinpal':
                service = ZarinPalPaymentService()
                return service.verify_payment(authority, amount)
            else:
                return {
                    'success': False,
                    'error': f'درگاه پرداخت {gateway_type} پشتیبانی نمی‌شود'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'خطا در تایید پرداخت: {str(e)}'
            }
    
    @staticmethod
    def get_payment_status(payment_request_id):
        """دریافت وضعیت پرداخت"""
        try:
            payment_request = PaymentRequest.objects.get(id=payment_request_id)
            return {
                'success': True,
                'status': payment_request.status,
                'amount': payment_request.amount,  # مبلغ به تومان
                'authority': payment_request.authority,
                'ref_id': payment_request.ref_id,
                'created_at': payment_request.created_at,
                'completed_at': payment_request.completed_at,
                'is_expired': payment_request.is_expired()
            }
        except PaymentRequest.DoesNotExist:
            return {
                'success': False,
                'error': 'درخواست پرداخت یافت نشد'
            } 