import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django_jalali.db import models as jmodels
from django.core.paginator import Paginator
from django.utils import timezone
from django.urls import reverse
from user.models import User
from .models import PaymentRequest, PaymentGateway
from wallet.models import Wallet, Transaction
from reservations.models import Reservation
from .services import PaymentService


@login_required
def payment_dashboard(request):
    """داشبورد پرداخت‌ها"""
    # دریافت درخواست‌های پرداخت کاربر
    payment_requests = PaymentRequest.objects.filter(
        user=request.user
    ).select_related('gateway', 'transaction').order_by('-created_at')[:10]
    
    # آمار پرداخت‌ها
    total_payments = PaymentRequest.objects.filter(user=request.user).count()
    successful_payments = PaymentRequest.objects.filter(
        user=request.user, 
        status='completed'
    ).count()
    pending_payments = PaymentRequest.objects.filter(
        user=request.user, 
        status__in=['pending', 'processing']
    ).count()
    
    # درگاه‌های پرداخت فعال
    active_gateways = PaymentGateway.objects.filter(is_active=True)
    
    context = {
        'payment_requests': payment_requests,
        'total_payments': total_payments,
        'successful_payments': successful_payments,
        'pending_payments': pending_payments,
        'active_gateways': active_gateways,
    }
    
    return render(request, 'payments/dashboard.html', context)


@login_required
def payment_list(request):
    """لیست پرداخت‌ها"""
    status = request.GET.get('status')
    gateway_type = request.GET.get('gateway_type')
    
    payments = PaymentRequest.objects.filter(
        user=request.user
    ).select_related('gateway', 'transaction').order_by('-created_at')
    
    # فیلترها
    if status:
        payments = payments.filter(status=status)
    
    if gateway_type:
        payments = payments.filter(gateway__gateway_type=gateway_type)
    
    # صفحه‌بندی
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'payments': page_obj,
        'status': status,
        'gateway_type': gateway_type,
    }
    
    return render(request, 'payments/payment_list.html', context)


@login_required
def payment_detail(request, payment_id):
    """جزئیات پرداخت"""
    payment_request = get_object_or_404(
        PaymentRequest, 
        id=payment_id, 
        user=request.user
    )
    
    # لاگ‌های پرداخت
    logs = PaymentLog.objects.filter(
        payment_request=payment_request
    ).order_by('-created_at')
    
    context = {
        'payment_request': payment_request,
        'logs': logs,
    }
    
    return render(request, 'payments/payment_detail.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def create_payment(request):
    """ایجاد پرداخت جدید"""
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            description = request.POST.get('description', '').strip()
            gateway_type = request.POST.get('gateway_type', 'zarinpal')
            callback_url = request.POST.get('callback_url', '')
            
            # اعتبارسنجی
            if amount <= 0:
                messages.error(request, 'مبلغ باید بیشتر از صفر باشد.')
                return render(request, 'payments/create_payment.html')
            
            if not description:
                messages.error(request, 'توضیحات را وارد کنید.')
                return render(request, 'payments/create_payment.html')
            
            # ایجاد پرداخت
            result = PaymentService.create_payment(
                user=request.user,
                amount=amount,
                description=description,
                gateway_type=gateway_type,
                callback_url=callback_url
            )
            
            if result['success']:
                # هدایت به درگاه پرداخت
                return redirect(result['startpay_url'])
            else:
                messages.error(request, result['error'])
                
        except (ValueError, TypeError):
            messages.error(request, 'مبلغ وارد شده نامعتبر است.')
        except Exception as e:
            messages.error(request, f'خطای سیستمی: {str(e)}')
    
    # درگاه‌های پرداخت فعال
    active_gateways = PaymentGateway.objects.filter(is_active=True)
    
    context = {
        'active_gateways': active_gateways,
    }
    
    return render(request, 'payments/create_payment.html', context)


@login_required
def wallet_deposit_payment(request):
    """پرداخت برای شارژ کیف پول"""
    # دریافت پارامترهای اختیاری از URL
    suggested_amount = request.GET.get('amount')
    redirect_to = request.GET.get('redirect_to')
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            gateway_type = request.POST.get('gateway_type', 'zarinpal')
            
            # اعتبارسنجی مبلغ
            if amount < Decimal('1000'):
                messages.error(request, 'حداقل مبلغ واریز ۱۰۰۰ تومان است.')
                return render(request, 'payments/wallet_deposit.html', {
                    'suggested_amount': suggested_amount, 
                    'redirect_to': redirect_to
                })
            
            if amount > Decimal('50000000'):
                messages.error(request, 'حداکثر مبلغ واریز ۵۰ میلیون تومان است.')
                return render(request, 'payments/wallet_deposit.html', {
                    'suggested_amount': suggested_amount, 
                    'redirect_to': redirect_to
                })
            
            # آدرس بازگشت
            callback_url = request.build_absolute_uri(
                reverse('payments:payment_callback')
            )
            
            if redirect_to:
                callback_url += f'?redirect_to={redirect_to}'
            
            # ایجاد پرداخت
            result = PaymentService.create_payment(
                user=request.user,
                amount=amount,
                description=f'واریز {amount} تومان به کیف پول',
                gateway_type=gateway_type,
                callback_url=callback_url,
                metadata={'type': 'wallet_deposit', 'redirect_to': redirect_to}
            )
            
            if result['success']:
                # هدایت به درگاه پرداخت
                return redirect(result['startpay_url'])
            else:
                messages.error(request, result['error'])
                
        except (ValueError, TypeError):
            messages.error(request, 'مبلغ وارد شده نامعتبر است.')
        except Exception as e:
            messages.error(request, f'خطای سیستمی: {str(e)}')
    
    # درگاه‌های پرداخت فعال
    active_gateways = PaymentGateway.objects.filter(is_active=True)
    
    context = {
        'min_amount': 1000,
        'max_amount': 50000000,
        'suggested_amount': suggested_amount,
        'redirect_to': redirect_to,
        'active_gateways': active_gateways,
    }
    
    return render(request, 'payments/wallet_deposit.html', context)


@login_required
def reservation_payment(request, reservation_id):
    """پرداخت برای رزرو نوبت"""
    reservation = get_object_or_404(
        Reservation, 
        id=reservation_id, 
        status='pending', 
        payment_status='pending'
    )
    
    # بررسی مالکیت رزرو
    if not (reservation.patient.user == request.user or 
            (hasattr(request.user, 'patient') and reservation.patient == request.user.patient)):
        messages.error(request, 'شما مجاز به مشاهده این صفحه نیستید.')
        return redirect('home')
    
    # محاسبه مبلغ نهایی (با تخفیف)
    final_amount = reservation.amount
    discount_info = None
    
    if hasattr(reservation, 'discount_usage'):
        discount_usage = reservation.discount_usage
        final_amount = discount_usage.final_amount
        discount_info = {
            'original_amount': discount_usage.original_amount,
            'discount_amount': discount_usage.discount_amount,
            'final_amount': discount_usage.final_amount,
            'discount_title': discount_usage.discount.title
        }
    
    if request.method == 'POST':
        gateway_type = request.POST.get('gateway_type', 'zarinpal')
        
        try:
            # آدرس بازگشت
            callback_url = request.build_absolute_uri(
                reverse('payments:payment_callback')
            )
            
            # ایجاد پرداخت
            result = PaymentService.create_payment(
                user=request.user,
                amount=final_amount,
                description=f"پرداخت نوبت پزشک {reservation.doctor} در تاریخ {reservation.day.date}",
                gateway_type=gateway_type,
                callback_url=callback_url,
                metadata={
                    'type': 'reservation_payment',
                    'reservation_id': reservation.id,
                    'doctor_id': reservation.doctor.id,
                    'discount_applied': discount_info is not None
                }
            )
            
            if result['success']:
                # ربط درخواست پرداخت به رزرو
                reservation.payment_request = result['payment_request']
                reservation.save()
                
                # هدایت به درگاه پرداخت
                return redirect(result['startpay_url'])
            else:
                messages.error(request, result['error'])
                
        except Exception as e:
            messages.error(request, f'خطای سیستمی: {str(e)}')
    
    # درگاه‌های پرداخت فعال
    active_gateways = PaymentGateway.objects.filter(is_active=True)
    
    context = {
        'reservation': reservation,
        'final_amount': final_amount,
        'discount_info': discount_info,
        'active_gateways': active_gateways,
    }
    
    return render(request, 'payments/reservation_payment.html', context)


@csrf_exempt
def payment_callback(request):
    """پاسخ از درگاه پرداخت"""
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')
    redirect_to = request.GET.get('redirect_to')
    
    if not authority:
        return render(request, 'payments/payment_response.html', {
            'message': 'خطا در پردازش پرداخت',
            'payment_request': None
        })
    
    try:
        # یافتن درخواست پرداخت
        payment_request = PaymentRequest.objects.get(authority=authority)
        
        if status == 'OK':
            # تایید پرداخت
            result = PaymentService.verify_payment(
                authority=authority,
                amount=payment_request.amount
            )
            
            if result['success']:
                # بررسی نوع پرداخت و هدایت مناسب
                payment_type = payment_request.metadata.get('type')
                
                if payment_type == 'reservation_payment':
                    # تایید رزرو
                    reservation_id = payment_request.metadata.get('reservation_id')
                    if reservation_id:
                        try:
                            reservation = Reservation.objects.get(id=reservation_id)
                            reservation.payment_status = 'paid'
                            reservation.status = 'confirmed'
                            
                            # Link the payment request to the reservation
                            reservation.payment_request = payment_request
                            reservation.save()
                            
                            # Send confirmation notification
                            if reservation.patient and reservation.patient.user:
                                from utils.utils import send_notification
                                message = f"نوبت شما با دکتر {reservation.doctor.user.get_full_name()} در تاریخ {reservation.day.date} ساعت {reservation.time} تایید شد. پرداخت با موفقیت انجام شد."
                                send_notification(
                                    user=reservation.patient.user,
                                    title='تایید نوبت و پرداخت',
                                    message=message,
                                    notification_type='success'
                                )
                            
                            messages.success(request, 'پرداخت با موفقیت انجام شد و نوبت شما تایید گردید.')
                            return redirect('reservations:view_appointment', pk=reservation.id)
                        except Reservation.DoesNotExist:
                            messages.error(request, 'رزرو مورد نظر یافت نشد.')
                            return redirect('home')
                
                # نمایش صفحه موفقیت
                return render(request, 'payments/payment_response.html', {
                    'message': 'پرداخت با موفقیت انجام شد',
                    'payment_request': payment_request
                })
            else:
                payment_request.mark_as_failed(result.get('error', 'خطای نامشخص'))
                return render(request, 'payments/payment_response.html', {
                    'message': 'پرداخت ناموفق بود',
                    'payment_request': payment_request
                })
        else:
            payment_request.mark_as_failed('کاربر پرداخت را لغو کرد')
            return render(request, 'payments/payment_response.html', {
                'message': 'پرداخت لغو شد',
                'payment_request': payment_request
            })
    
    except PaymentRequest.DoesNotExist:
        return render(request, 'payments/payment_response.html', {
            'message': 'درخواست پرداخت یافت نشد',
            'payment_request': None
        })
    except Exception as e:
        return render(request, 'payments/payment_response.html', {
            'message': f'خطا در پردازش پاسخ پرداخت: {str(e)}',
            'payment_request': None
        })


# API Endpoints
@login_required
def api_payment_status(request, payment_id):
    """API دریافت وضعیت پرداخت"""
    try:
        payment_request = PaymentRequest.objects.get(
            id=payment_id, 
            user=request.user
        )
        
        return JsonResponse({
            'success': True,
            'status': payment_request.status,
            'amount': float(payment_request.amount),
            'authority': payment_request.authority,
            'ref_id': payment_request.ref_id,
            'created_at': payment_request.created_at.isoformat(),
            'completed_at': payment_request.completed_at.isoformat() if payment_request.completed_at else None,
            'is_expired': payment_request.is_expired()
        })
    except PaymentRequest.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'درخواست پرداخت یافت نشد'
        })


@login_required
def api_create_payment(request):
    """API ایجاد پرداخت"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = Decimal(data.get('amount', '0'))
            description = data.get('description', '').strip()
            gateway_type = data.get('gateway_type', 'zarinpal')
            callback_url = data.get('callback_url', '')
            metadata = data.get('metadata', {})
            
            # اعتبارسنجی
            if amount <= 0:
                return JsonResponse({
                    'success': False,
                    'error': 'مبلغ باید بیشتر از صفر باشد'
                })
            
            if not description:
                return JsonResponse({
                    'success': False,
                    'error': 'توضیحات را وارد کنید'
                })
            
            # ایجاد پرداخت
            result = PaymentService.create_payment(
                user=request.user,
                amount=amount,
                description=description,
                gateway_type=gateway_type,
                callback_url=callback_url,
                metadata=metadata
            )
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'authority': result['authority'],
                    'startpay_url': result['startpay_url'],
                    'payment_request_id': result['payment_request'].id
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'داده‌های ارسالی نامعتبر است'
            })
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'مبلغ وارد شده نامعتبر است'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'خطای سیستمی: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'متد نامعتبر'
    })


@login_required
def api_verify_payment(request):
    """API تایید پرداخت"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            authority = data.get('authority')
            amount = Decimal(data.get('amount', '0'))
            
            if not authority:
                return JsonResponse({
                    'success': False,
                    'error': 'کد Authority الزامی است'
                })
            
            # تایید پرداخت
            result = PaymentService.verify_payment(
                authority=authority,
                amount=amount
            )
            
            return JsonResponse(result)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'داده‌های ارسالی نامعتبر است'
            })
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'مبلغ وارد شده نامعتبر است'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'خطای سیستمی: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'متد نامعتبر'
    }) 