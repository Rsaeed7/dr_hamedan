import json
import logging
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
from .models import PaymentRequest, PaymentGateway, PaymentLog
from wallet.models import Wallet, Transaction
from reservations.models import Reservation
from .services import PaymentService, CurrencyConverter

logger = logging.getLogger(__name__)


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
            amount = int(request.POST.get('amount', '0'))
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

            amount = int(request.POST.get('amount', '0'))
            gateway_type = request.POST.get('gateway_type', 'zarinpal')
            
            # اعتبارسنجی مبلغ
            if amount < int('1000'):
                messages.error(request, 'حداقل مبلغ واریز ۱۰۰۰ تومان است.')
                return render(request, 'payments/wallet_deposit.html', {
                    'suggested_amount': suggested_amount, 
                    'redirect_to': redirect_to
                })
            
            if amount > int('50000000'):
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
    # CRITICAL FIX: For direct payment, reservation is still 'available'
    # Check session for booking intent instead of reservation status
    booking_data = request.session.get('pending_direct_booking', {})
    
    # Get reservation - it should still be available for direct payment
    try:
        reservation = Reservation.objects.get(id=reservation_id)
    except Reservation.DoesNotExist:
        messages.error(request, 'رزرو مورد نظر یافت نشد')
        return redirect('doctors:doctor_list')
    
    # Check if this is a valid pending direct booking
    if booking_data.get('reservation_id') != reservation_id:
        messages.error(request, 'اطلاعات رزرو یافت نشد. لطفاً از ابتدا اقدام کنید')
        return redirect('reservations:book_appointment', doctor_slug=reservation.doctor.slug)
    
    # Check if slot is still available
    if not reservation.is_available():
        messages.error(request, 'این نوبت دیگر در دسترس نیست. لطفاً نوبت دیگری انتخاب کنید')
        return redirect('reservations:book_appointment', doctor_slug=reservation.doctor.slug)
    
    # محاسبه مبلغ نهایی بر اساس تعرفه پزشک
    original_amount = reservation.doctor.consultation_fee
    final_amount = original_amount
    discount_info = None
    
    # Note: Discount checking removed for direct payment flow since reservation
    # doesn't have patient data yet. Discounts are applied during wallet payment.
    
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
                # CRITICAL FIX: Don't link payment_request to reservation yet
                # The reservation is still 'available' and will be locked in payment callback
                # Just redirect to payment gateway
                return redirect(result['startpay_url'])
            else:
                messages.error(request, result['error'])
                
        except Exception as e:
            messages.error(request, f'خطای سیستمی: {str(e)}')
    
    # درگاه‌های پرداخت فعال
    active_gateways = PaymentGateway.objects.filter(is_active=True)
    
    # Get patient data from session for display
    patient_data = booking_data.get('patient_data', {})
    
    context = {
        'reservation': reservation,
        'final_amount': final_amount,
        'discount_info': discount_info,
        'active_gateways': active_gateways,
        'patient_name': patient_data.get('name', ''),
        'booking_date': booking_data.get('date', ''),
        'booking_time': booking_data.get('time', ''),
    }
    
    return render(request, 'payments/reservation_payment.html', context)


@login_required
def chat_payment(request, chat_request_id):
    """پرداخت برای مشاوره آنلاین"""
    from chatmed.models import ChatRequest
    from doctors.models import Doctor
    
    # CRITICAL FIX: Check if this is a session-based request (direct payment)
    chat_request_data = request.session.get('pending_chat_request', {})
    
    if chat_request_id == 0 or chat_request_data:
        # Session-based chat request (direct payment flow)
        if not chat_request_data:
            messages.error(request, 'اطلاعات درخواست یافت نشد. لطفاً از ابتدا اقدام کنید')
            return redirect('chat:list_doctors')
        
        # Get doctor and validate
        try:
            doctor = Doctor.objects.get(id=chat_request_data['doctor_id'])
        except Doctor.DoesNotExist:
            messages.error(request, 'پزشک مورد نظر یافت نشد')
            return redirect('chat:list_doctors')
        
        # محاسبه مبلغ نهایی from session data
        final_amount = chat_request_data.get('amount', doctor.online_visit_fee)
        patient_name = chat_request_data.get('patient_name', '')
        disease_summary = chat_request_data.get('disease_summary', '')
        
        # Create a temporary object for display (not saved to DB)
        chat_request = type('obj', (object,), {
            'id': None,  # No ID yet - session-based request
            'doctor': doctor,
            'amount': final_amount,
            'patient_name': patient_name,
            'disease_summary': disease_summary
        })()
    else:
        # Database-based chat request (wallet payment flow or retry)
        chat_request = get_object_or_404(
            ChatRequest, 
            id=chat_request_id, 
            payment_status='pending'
        )
        
        # بررسی مالکیت درخواست
        if not (chat_request.patient.user == request.user or 
                (hasattr(request.user, 'patient') and chat_request.patient == request.user.patient)):
            messages.error(request, 'شما مجاز به مشاهده این صفحه نیستید.')
            return redirect('home')
        
        # محاسبه مبلغ نهایی
        final_amount = chat_request.amount
    
    if request.method == 'POST':
        gateway_type = request.POST.get('gateway_type', 'zarinpal')
        
        try:
            # آدرس بازگشت
            callback_url = request.build_absolute_uri(
                reverse('payments:payment_callback')
            )
            
            # Prepare metadata
            metadata = {
                'type': 'chat_payment',
                'doctor_id': chat_request.doctor.id,
            }
            
            # For session-based requests, include session data in metadata
            if chat_request_id == 0 or chat_request_data:
                metadata['is_session_based'] = True
                # Don't include chat_request_id since it doesn't exist yet
            else:
                metadata['chat_request_id'] = chat_request.id
                metadata['is_session_based'] = False
            
            # ایجاد پرداخت
            result = PaymentService.create_payment(
                user=request.user,
                amount=final_amount,
                description=f"پرداخت مشاوره آنلاین دکتر {chat_request.doctor}",
                gateway_type=gateway_type,
                callback_url=callback_url,
                metadata=metadata
            )
            
            if result['success']:
                # CRITICAL FIX: For session-based requests, DON'T link to ChatRequest yet
                # For database-based requests (wallet), link the payment
                if not (chat_request_id == 0 or chat_request_data):
                    chat_request.payment_request = result['payment_request']
                    chat_request.save()
                
                # هدایت به درگاه پرداخت
                return redirect(result['startpay_url'])
            else:
                messages.error(request, result['error'])
                
        except Exception as e:
            messages.error(request, f'خطای سیستمی: {str(e)}')
    
    # درگاه‌های پرداخت فعال
    active_gateways = PaymentGateway.objects.filter(is_active=True)
    
    context = {
        'chat_request': chat_request,
        'final_amount': final_amount,
        'active_gateways': active_gateways,
    }
    
    return render(request, 'payments/chat_payment.html', context)


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
                    # CRITICAL FIX: Lock reservation ONLY after successful payment
                    reservation_id = payment_request.metadata.get('reservation_id')
                    if reservation_id:
                        try:
                            from django.db import transaction as db_transaction
                            from patients.models import PatientsFile
                            
                            # Get booking data from session
                            booking_data = request.session.get('pending_direct_booking', {})
                            
                            with db_transaction.atomic():
                                # Lock the reservation with select_for_update to prevent race conditions
                                reservation = Reservation.objects.select_for_update().get(id=reservation_id)
                                
                                # Check if slot is still available
                                if not reservation.is_available():
                                    # Slot was taken by someone else
                                    payment_request.mark_as_failed('نوبت توسط شخص دیگری رزرو شده است')
                                    messages.error(request, 'متأسفانه این نوبت توسط شخص دیگری رزرو شده است. مبلغ به کیف پول شما برگشت داده خواهد شد.')
                                    
                                    # Refund to wallet
                                    from wallet.models import Wallet, Transaction as WalletTransaction
                                    wallet, _ = Wallet.objects.get_or_create(user=request.user)
                                    wallet.add_balance(payment_request.amount)
                                    WalletTransaction.objects.create(
                                        user=request.user,
                                        wallet=wallet,
                                        amount=payment_request.amount,
                                        transaction_type='refund',
                                        payment_method='wallet',
                                        status='completed',
                                        description=f'بازگشت وجه رزرو ناموفق - نوبت {reservation.id}'
                                    )
                                    
                                    return render(request, 'payments/payment_response.html', {
                                        'message': 'نوبت توسط شخص دیگری رزرو شده است',
                                        'payment_request': payment_request,
                                        'show_retry': True,
                                        'doctor_slug': booking_data.get('doctor_slug')
                                    })
                                
                                # Slot is still available - lock it now
                                if booking_data:
                                    patient_data = booking_data.get('patient_data', {})
                                    reservation.patient_name = patient_data.get('name', '')
                                    reservation.phone = patient_data.get('phone', '')
                                    reservation.patient_national_id = patient_data.get('national_id', '')
                                    reservation.patient_email = patient_data.get('email', '')
                                    reservation.notes = patient_data.get('notes', '')
                                    
                                    # Create or link patient file
                                    patient, _ = PatientsFile.objects.get_or_create(
                                        user=request.user,
                                        defaults={
                                            'phone': patient_data.get('phone', ''),
                                            'email': request.user.email,
                                            'national_id': patient_data.get('national_id', '')
                                        }
                                    )
                                    reservation.patient = patient
                                
                                # Now lock the reservation
                                reservation.payment_status = 'paid'
                                reservation.status = 'confirmed'
                                reservation.payment_request = payment_request
                                reservation.save()
                                
                                # Clear session data
                                if 'pending_direct_booking' in request.session:
                                    del request.session['pending_direct_booking']
                                
                                # Send confirmation notification to patient
                                if reservation.patient and reservation.patient.user:
                                    from utils.utils import send_notification
                                    message = f"نوبت شما با دکتر {reservation.doctor.user.get_full_name()} در تاریخ {reservation.day.date} ساعت {reservation.time} تایید شد. پرداخت با موفقیت انجام شد."
                                    send_notification(
                                        user=reservation.patient.user,
                                        title='تایید نوبت و پرداخت',
                                        message=message,
                                        notification_type='success'
                                    )
                            
                            # Send SMS notification to doctor
                            if reservation.doctor and reservation.doctor.user:
                                from utils.sms_service import sms_service
                                doctor_phone = reservation.doctor.user.phone
                                if doctor_phone:
                                    from jdatetime import datetime as jdatetime_dt
                                    jalali_date = jdatetime_dt.fromgregorian(datetime=reservation.day.date).strftime('%Y/%m/%d')
                                    
                                    doctor_sms_message = f"""دکتر {reservation.doctor.user.get_full_name()} عزیز
نوبت جدیدی برای شما ثبت شد:
بیمار: {reservation.patient_name}
تاریخ: {jalali_date}
ساعت: {reservation.time.strftime('%H:%M')}
مبلغ: {reservation.amount:,} تومان
وضعیت پرداخت: پرداخت شده
دکتر همدان"""
                                    
                                    try:
                                        sms_service.send_sms(doctor_phone, doctor_sms_message)
                                        logger.info(f"SMS sent to doctor {reservation.doctor.id} for reservation {reservation.id}")
                                    except Exception as e:
                                        logger.error(f"Failed to send SMS to doctor: {str(e)}")
                            
                            messages.success(request, 'پرداخت با موفقیت انجام شد و نوبت شما تایید گردید.')
                            return redirect('reservations:view_appointment', pk=reservation.id)
                        except Reservation.DoesNotExist:
                            messages.error(request, 'رزرو مورد نظر یافت نشد.')
                            return redirect('home')
                
                elif payment_type == 'chat_payment':
                    # CRITICAL FIX: Create ChatRequest ONLY after successful payment
                    from chatmed.models import ChatRequest
                    from doctors.models import Doctor
                    from patients.models import PatientsFile
                    from django.db import transaction as db_transaction
                    
                    is_session_based = payment_request.metadata.get('is_session_based', False)
                    
                    if is_session_based:
                        # Session-based chat request - create it NOW after payment success
                        chat_request_data = request.session.get('pending_chat_request', {})
                        
                        if chat_request_data:
                            try:
                                with db_transaction.atomic():
                                    # Get doctor and patient
                                    doctor = Doctor.objects.get(id=chat_request_data['doctor_id'])
                                    patient = PatientsFile.objects.get(id=chat_request_data['patient_id'])
                                    
                                    # NOW create the ChatRequest (payment confirmed!)
                                    chat_request = ChatRequest.objects.create(
                                        patient=patient,
                                        doctor=doctor,
                                        disease_summary=chat_request_data.get('disease_summary', ''),
                                        amount=chat_request_data.get('amount', 0),
                                        patient_name=chat_request_data.get('patient_name', ''),
                                        patient_national_id=chat_request_data.get('patient_national_id', ''),
                                        phone=chat_request_data.get('phone', ''),
                                        payment_status='paid',
                                        payment_request=payment_request
                                    )
                                    
                                    # Clear session data
                                    if 'pending_chat_request' in request.session:
                                        del request.session['pending_chat_request']
                                    
                                    # Send confirmation notification
                                    if patient.user:
                                        from utils.utils import send_notification
                                        message = f"درخواست مشاوره آنلاین شما با دکتر {doctor.user.get_full_name()} تایید شد. پرداخت با موفقیت انجام شد."
                                        send_notification(
                                            user=patient.user,
                                            title='تایید مشاوره آنلاین',
                                            message=message,
                                            notification_type='success'
                                        )
                                    
                                    messages.success(request, 'پرداخت با موفقیت انجام شد و درخواست مشاوره شما ثبت گردید.')
                                    return redirect('chat:request_status', request_id=chat_request.id)
                            except Exception as e:
                                messages.error(request, f'خطا در ثبت درخواست: {str(e)}')
                                return redirect('chat:list_doctors')
                        else:
                            messages.error(request, 'اطلاعات درخواست یافت نشد')
                            return redirect('chat:list_doctors')
                    else:
                        # Database-based chat request (wallet payment)
                        chat_request_id = payment_request.metadata.get('chat_request_id')
                        if chat_request_id:
                            try:
                                chat_request = ChatRequest.objects.get(id=chat_request_id)
                                chat_request.payment_status = 'paid'
                                
                                # Link the payment request to the chat request
                                chat_request.payment_request = payment_request
                                chat_request.save()
                                
                                # Send confirmation notification to patient
                                if chat_request.patient and chat_request.patient.user:
                                    from utils.utils import send_notification
                                    message = f"درخواست مشاوره آنلاین شما با دکتر {chat_request.doctor.user.get_full_name()} تایید شد. پرداخت با موفقیت انجام شد."
                                    send_notification(
                                        user=chat_request.patient.user,
                                        title='تایید مشاوره آنلاین',
                                        message=message,
                                        notification_type='success'
                                    )
                                
                                # Send SMS notification to doctor
                                if chat_request.doctor and chat_request.doctor.user:
                                    from utils.sms_service import sms_service
                                    doctor_phone = chat_request.doctor.user.phone
                                    if doctor_phone:
                                        from jdatetime import datetime as jdatetime_dt
                                        jalali_datetime = jdatetime_dt.now().strftime('%Y/%m/%d %H:%M')
                                        
                                        doctor_sms_message = f"""دکتر {chat_request.doctor.user.get_full_name()} عزیز
درخواست مشاوره آنلاین جدید:
بیمار: {chat_request.patient_name}
تاریخ درخواست: {jalali_datetime}
مبلغ: {chat_request.amount:,} تومان
وضعیت پرداخت: پرداخت شده
لطفا به پنل مشاوره‌های آنلاین مراجعه کنید.
دکتر همدان"""
                                        
                                        try:
                                            sms_service.send_sms(doctor_phone, doctor_sms_message)
                                            logger.info(f"SMS sent to doctor {chat_request.doctor.id} for chat request {chat_request.id}")
                                        except Exception as e:
                                            logger.error(f"Failed to send SMS to doctor: {str(e)}")
                                
                                messages.success(request, 'پرداخت با موفقیت انجام شد و درخواست مشاوره شما ثبت گردید.')
                                return redirect('chat:request_status', request_id=chat_request.id)
                            except ChatRequest.DoesNotExist:
                                messages.error(request, 'درخواست مشاوره یافت نشد.')
                                return redirect('chat:list_doctors')
                
                # نمایش صفحه موفقیت
                return render(request, 'payments/payment_response.html', {
                    'message': 'پرداخت با موفقیت انجام شد',
                    'payment_request': payment_request
                })
            else:
                payment_request.mark_as_failed(result.get('error', 'خطای نامشخص'))
                
                # Check payment type and provide retry option
                payment_type = payment_request.metadata.get('type')
                booking_data = request.session.get('pending_direct_booking', {})
                chat_data = request.session.get('pending_chat_request', {})
                
                context = {
                    'message': 'پرداخت ناموفق بود',
                    'payment_request': payment_request,
                    'error_detail': result.get('error', 'خطای نامشخص')
                }
                
                if payment_type == 'reservation_payment' and booking_data:
                    context.update({
                        'show_retry': True,
                        'reservation_id': booking_data.get('reservation_id'),
                        'doctor_slug': booking_data.get('doctor_slug'),
                        'is_reservation_payment': True
                    })
                elif payment_type == 'chat_payment' and chat_data:
                    context.update({
                        'show_retry': True,
                        'is_chat_payment': True
                    })
                
                return render(request, 'payments/payment_response.html', context)
        else:
            payment_request.mark_as_failed('کاربر پرداخت را لغو کرد')
            
            # Check payment type and provide retry option
            payment_type = payment_request.metadata.get('type')
            booking_data = request.session.get('pending_direct_booking', {})
            chat_data = request.session.get('pending_chat_request', {})
            
            context = {
                'message': 'پرداخت لغو شد',
                'payment_request': payment_request
            }
            
            if payment_type == 'reservation_payment' and booking_data:
                context.update({
                    'show_retry': True,
                    'reservation_id': booking_data.get('reservation_id'),
                    'doctor_slug': booking_data.get('doctor_slug'),
                    'is_reservation_payment': True
                })
            elif payment_type == 'chat_payment' and chat_data:
                context.update({
                    'show_retry': True,
                    'is_chat_payment': True
                })
            
            return render(request, 'payments/payment_response.html', context)
    
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
def retry_reservation_payment(request, reservation_id):
    """صفحه تلاش مجدد برای پرداخت رزرو نوبت"""
    try:
        from reservations.models import Reservation
        
        # Get reservation
        reservation = Reservation.objects.get(id=reservation_id)
        
        # Check if reservation is still available
        if not reservation.is_available():
            messages.error(request, 'این نوبت دیگر در دسترس نیست')
            return redirect('doctors:doctor_detail', slug=reservation.doctor.slug)
        
        # Check if we have booking data in session
        booking_data = request.session.get('pending_direct_booking', {})
        if not booking_data or booking_data.get('reservation_id') != reservation_id:
            messages.error(request, 'اطلاعات رزرو یافت نشد. لطفاً از ابتدا اقدام کنید')
            doctor_slug = reservation.doctor.slug if hasattr(reservation, 'doctor') else 'default'
            return redirect('reservations:book_appointment', doctor_slug=doctor_slug)
        
        # Redirect to payment page
        return redirect('payments:reservation_payment', reservation_id=reservation_id)
        
    except Reservation.DoesNotExist:
        messages.error(request, 'رزرو مورد نظر یافت نشد')
        return redirect('doctors:doctor_list')
    except Exception as e:
        messages.error(request, f'خطا در پردازش درخواست: {str(e)}')
        return redirect('doctors:doctor_list')


@login_required
def retry_chat_payment(request):
    """صفحه تلاش مجدد برای پرداخت مشاوره آنلاین"""
    # Check if we have chat request data in session
    chat_data = request.session.get('pending_chat_request', {})
    
    if not chat_data:
        messages.error(request, 'اطلاعات درخواست مشاوره یافت نشد. لطفاً از ابتدا اقدام کنید')
        return redirect('chat:list_doctors')
    
    # Redirect to payment page (use ID 0 for session-based)
    return redirect('payments:chat_payment', chat_request_id=0)


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
            # مبلغ به تومان
            'amount': payment_request.amount,
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
            # مبلغ به تومان
            amount = int(data.get('amount', '0'))
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
            amount = int(data.get('amount', '0'))
            
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