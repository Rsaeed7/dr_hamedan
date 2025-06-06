import jdatetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction as db_transaction
from django.db.models import Q, Sum
from django.utils import timezone
from django.core.paginator import Paginator
from decimal import Decimal
import json
import uuid

from .models import Transaction, Wallet, PaymentGateway
from reservations.models import Reservation
from discounts.models import DiscountUsage


@login_required
def wallet_dashboard(request):
    """داشبورد کیف پول کاربر"""
    # دریافت یا ایجاد کیف پول کاربر
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # دریافت تراکنش‌های اخیر
    recent_transactions = Transaction.objects.filter(
        user=request.user
    ).select_related('gateway', 'related_transaction').order_by('-created_at')[:5]
    
    # محاسبه آمار
    completed_transactions = Transaction.objects.filter(
        user=request.user, status='completed'
    )
    
    total_deposits = completed_transactions.filter(
        transaction_type__in=['deposit', 'refund', 'bonus']
    ).aggregate(total=Sum('net_amount'))['total'] or Decimal('0')
    
    total_withdrawals = completed_transactions.filter(
        transaction_type__in=['withdrawal', 'payment', 'commission', 'penalty']
    ).aggregate(total=Sum('net_amount'))['total'] or Decimal('0')
    
    pending_transactions = Transaction.objects.filter(
        user=request.user, status__in=['pending', 'processing']
    ).count()
    
    context = {
        'wallet': wallet,
        'recent_transactions': recent_transactions,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'pending_transactions': pending_transactions,
        'balance': wallet.balance,
    }
    
    return render(request, 'wallet/wallet.html', context)


@login_required
def transaction_list(request):
    transaction_type = request.GET.get('transaction_type')
    status = request.GET.get('status')

    from_date_str = request.GET.get('from')
    to_date_str = request.GET.get('to')

    transactions = Transaction.objects.filter(user=request.user).select_related('gateway', 'related_transaction').order_by('-created_at')

    # فیلتر نوع تراکنش
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    # فیلتر وضعیت
    if status:
        transactions = transactions.filter(status=status)

    # فیلتر تاریخ از (from)
    if from_date_str:
        try:
            from_jdate = jdatetime.datetime.strptime(from_date_str, "%Y-%m-%d").togregorian()
            transactions = transactions.filter(created_at__date__gte=from_jdate.date())
        except Exception as e:
            print("خطای تبدیل تاریخ from:", e)

    # فیلتر تاریخ تا (to)
    if to_date_str:
        try:
            to_jdate = jdatetime.datetime.strptime(to_date_str, "%Y-%m-%d").togregorian()
            transactions = transactions.filter(created_at__date__lte=to_jdate.date())
        except Exception as e:
            print("خطای تبدیل تاریخ to:", e)

    # آمارها
    completed_count = transactions.filter(status='completed').count()
    pending_count = transactions.filter(status__in=['pending', 'processing']).count()

    # کیف پول
    wallet = get_object_or_404(Wallet, user=request.user)

    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'transactions': page_obj,
        'transaction_type': transaction_type,
        'status': status,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'balance': wallet.balance,
    }

    return render(request, 'wallet/translations.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def deposit(request):
    """واریز به کیف پول"""
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # دریافت پارامترهای اختیاری از URL
    suggested_amount = request.GET.get('amount')
    redirect_to = request.GET.get('redirect_to')
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            payment_method = request.POST.get('payment_method', 'gateway')
            
            # اعتبارسنجی مبلغ
            if amount < Decimal('1000'):
                messages.error(request, 'حداقل مبلغ واریز ۱۰۰۰ تومان است.')
                return render(request, 'wallet/wallet_deposit.html', {'wallet': wallet, 'suggested_amount': suggested_amount, 'redirect_to': redirect_to})
            
            if amount > Decimal('50000000'):
                messages.error(request, 'حداکثر مبلغ واریز ۵۰ میلیون تومان است.')
                return render(request, 'wallet/wallet_deposit.html', {'wallet': wallet, 'suggested_amount': suggested_amount, 'redirect_to': redirect_to})
            
            # انتخاب درگاه پرداخت
            gateway = PaymentGateway.objects.filter(is_active=True).first()
            if not gateway and payment_method == 'gateway':
                messages.error(request, 'درگاه پرداخت فعالی یافت نشد.')
                return render(request, 'wallet/wallet_deposit.html', {'wallet': wallet, 'suggested_amount': suggested_amount, 'redirect_to': redirect_to})
            
            # ایجاد تراکنش
            with db_transaction.atomic():
                transaction = Transaction.objects.create(
                    user=request.user,
                    wallet=wallet,
                    amount=amount,
                    transaction_type='deposit',
                    payment_method=payment_method,
                    gateway=gateway,
                    description=f'واریز {amount} تومان به کیف پول',
                    tracking_code=str(uuid.uuid4())[:12].upper()
                )
                
                # ذخیره آدرس بازگشت در تراکنش
                if redirect_to:
                    transaction.notes = f"redirect_to:{redirect_to}"
                    transaction.save()
                
                if payment_method == 'gateway' and gateway:
                    # هدایت به درگاه پرداخت
                    return redirect('wallet:payment_gateway', transaction_id=transaction.id)
                else:
                    # پردازش مستقیم (برای تست)
                    transaction.mark_as_completed()
                    messages.success(request, f'مبلغ {amount} تومان با موفقیت به کیف پول شما اضافه شد.')
                    
                    # اگر آدرس بازگشت وجود داشت، به آن هدایت شود
                    if redirect_to:
                        return redirect(redirect_to)
                    return redirect('wallet:wallet_dashboard')
        
        except (ValueError, TypeError):
            messages.error(request, 'مبلغ وارد شده نامعتبر است.')
        except Exception as e:
            messages.error(request, 'خطای سیستمی رخ داده است.')
    
    context = {
        'wallet': wallet,
        'min_amount': 1000,
        'max_amount': 50000000,
        'suggested_amount': suggested_amount,
        'redirect_to': redirect_to,
    }
    
    return render(request, 'wallet/wallet_deposit.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def withdraw(request):
    """برداشت از کیف پول"""
    wallet = get_object_or_404(Wallet, user=request.user)
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            bank_account = request.POST.get('bank_account', '').strip()
            
            # اعتبارسنجی
            if amount < Decimal('10000'):
                messages.error(request, 'حداقل مبلغ برداشت ۱۰ هزار تومان است.')
                return render(request, 'wallet/wallet_withdraw.html', {'wallet': wallet})
            
            if not wallet.can_withdraw(amount):
                messages.error(request, 'موجودی کافی در کیف پول شما وجود ندارد.')
                return render(request, 'wallet/wallet_withdraw.html', {'wallet': wallet})
            
            if not bank_account:
                messages.error(request, 'شماره حساب بانکی را وارد کنید.')
                return render(request, 'wallet/wallet_withdraw.html', {'wallet': wallet})
            
            # ایجاد تراکنش برداشت
            with db_transaction.atomic():
                transaction = Transaction.objects.create(
                    user=request.user,
                    wallet=wallet,
                    amount=amount,
                    transaction_type='withdrawal',
                    payment_method='transfer',
                    description=f'برداشت {amount} تومان از کیف پول',
                    tracking_code=str(uuid.uuid4())[:12].upper(),
                    metadata={'bank_account': bank_account}
                )
                
                # مسدود کردن موجودی
                if wallet.freeze_balance(amount):
                    messages.success(request, 
                        f'درخواست برداشت {amount} تومان ثبت شد. '
                        f'کد پیگیری: {transaction.tracking_code}'
                    )
                    return redirect('wallet:wallet_dashboard')
                else:
                    transaction.mark_as_failed('عدم موجودی کافی')
                    messages.error(request, 'خطا در پردازش درخواست برداشت.')
        
        except (ValueError, TypeError):
            messages.error(request, 'مبلغ وارد شده نامعتبر است.')
        except Exception as e:
            messages.error(request, 'خطای سیستمی رخ داده است.')
    
    context = {
        'wallet': wallet,
        'min_amount': 10000,
    }
    
    return render(request, 'wallet/wallet_withdraw.html', context)


def process_payment(request, reservation_id):
    """پردازش پرداخت برای رزرو"""
    # دریافت رزرو
    reservation = get_object_or_404(
        Reservation, 
        id=reservation_id, 
        status='pending', 
        payment_status='pending'
    )
    
    # بررسی مالکیت رزرو
    if request.user.is_authenticated:
        if not (reservation.patient.user == request.user or 
                (hasattr(request.user, 'patient') and reservation.patient == request.user.patient)):
            messages.error(request, 'شما مجاز به مشاهده این صفحه نیستید.')
            return redirect('home')
    
    # دریافت یا ایجاد کیف پول
    user = request.user if request.user.is_authenticated else reservation.patient.user
    wallet, created = Wallet.objects.get_or_create(user=user)
    
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
        payment_method = request.POST.get('payment_method', 'gateway')
        
        try:
            with db_transaction.atomic():
                # ایجاد تراکنش پرداخت
                transaction = Transaction.objects.create(
                    user=user,
                    wallet=wallet,
                    amount=final_amount,
                    transaction_type='payment',
                    payment_method=payment_method,
                    description=f"پرداخت نوبت پزشک {reservation.doctor} در تاریخ {reservation.day.date}",
                    tracking_code=str(uuid.uuid4())[:12].upper(),
                    metadata={
                        'reservation_id': reservation.id,
                        'doctor_id': reservation.doctor.id,
                        'discount_applied': discount_info is not None
                    }
                )
                
                # ربط تراکنش به رزرو
                reservation.transaction = transaction
                reservation.save()
                
                if payment_method == 'wallet':
                    # پرداخت از کیف پول
                    if wallet.can_withdraw(final_amount):
                        transaction.status = 'completed'
                        transaction.processed_at = timezone.now()
                        transaction.save()
                        
                        # کسر از کیف پول
                        wallet.subtract_balance(final_amount)
                        
                        # تایید رزرو
                        reservation.payment_status = 'paid'
                        reservation.status = 'confirmed'
                        reservation.save()
                        
                        messages.success(request, 'پرداخت با موفقیت انجام شد!')
                        return redirect('reservations:appointment_status', pk=reservation.id)
                    else:
                        transaction.mark_as_failed('موجودی کافی نیست')
                        messages.error(request, 'موجودی کیف پول شما کافی نیست.')
                
                elif payment_method == 'gateway':
                    # هدایت به درگاه پرداخت
                    return redirect('wallet:payment_gateway', transaction_id=transaction.id)
        
        except Exception as e:
            messages.error(request, 'خطای سیستمی رخ داده است.')
    
    # دریافت درگاه‌های پرداخت فعال
    active_gateways = PaymentGateway.objects.filter(is_active=True)
    
    context = {
        'reservation': reservation,
        'wallet': wallet,
        'final_amount': final_amount,
        'discount_info': discount_info,
        'active_gateways': active_gateways,
        'can_pay_with_wallet': wallet.can_withdraw(final_amount),
    }
    
    return render(request, 'wallet/payment.html', context)


def payment_gateway(request, transaction_id):
    """هدایت به درگاه پرداخت"""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # بررسی مالکیت تراکنش
    if request.user.is_authenticated and transaction.user != request.user:
        messages.error(request, 'دسترسی غیرمجاز.')
        return redirect('home')
    
    if not transaction.gateway:
        messages.error(request, 'درگاه پرداخت مشخص نشده است.')
        return redirect('wallet:wallet_dashboard')
    
    try:
        # ایجاد Authority برای پرداخت
        transaction.authority = str(uuid.uuid4())[:20].upper()
        transaction.save()
        
        # در حالت واقعی، اینجا باید درخواست به API درگاه پرداخت ارسال شود
        # برای دمو، مستقیماً به صفحه callback می‌رویم
        
        # شبیه‌سازی درگاه پرداخت
        callback_url = request.build_absolute_uri(
            reverse('wallet:payment_callback') + 
            f'?Authority={transaction.authority}&Status=OK'
        )
        
        # در محیط واقعی، اینجا باید به سایت درگاه پرداخت redirect شود
        return redirect(callback_url)
    
    except Exception as e:
        transaction.mark_as_failed('خطا در اتصال به درگاه پرداخت')
        messages.error(request, 'خطا در اتصال به درگاه پرداخت.')
        return redirect('wallet:wallet_dashboard')


@csrf_exempt
def payment_callback(request):
    """پاسخ از درگاه پرداخت"""
    # پارامترهای بازگشتی از درگاه
    status = request.GET.get('status', '')
    transaction_id = request.GET.get('transaction_id', '')
    
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        
        # بررسی وضعیت پرداخت
        if status == 'success':
            transaction.mark_as_completed()
            messages.success(request, f'پرداخت با موفقیت انجام شد و مبلغ {transaction.amount:,} تومان به کیف پول شما اضافه شد.')
            
            # بررسی آدرس بازگشت
            redirect_url = 'wallet:wallet_dashboard'
            if transaction.notes and transaction.notes.startswith('redirect_to:'):
                redirect_path = transaction.notes.replace('redirect_to:', '')
                if redirect_path:
                    return redirect(redirect_path)
        else:
            transaction.mark_as_failed()
            messages.error(request, 'پرداخت ناموفق بود. لطفاً دوباره تلاش کنید.')
            redirect_url = 'wallet:deposit'
    
    except Transaction.DoesNotExist:
        messages.error(request, 'تراکنش یافت نشد.')
        redirect_url = 'wallet:wallet_dashboard'
    except Exception as e:
        messages.error(request, f'خطا در پردازش پاسخ پرداخت: {str(e)}')
        redirect_url = 'wallet:wallet_dashboard'
    
    return redirect(redirect_url)


@login_required
def transaction_detail(request, transaction_id):
    """جزئیات تراکنش"""
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    context = {
        'transaction': transaction,
    }
    
    return render(request, 'wallet/transaction_detail.html', context)


@login_required
@require_http_methods(["POST"])
def request_refund(request, transaction_id):
    """درخواست بازگشت وجه"""
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    if not transaction.can_be_refunded():
        return JsonResponse({
            'success': False,
            'message': 'امکان بازگشت وجه برای این تراکنش وجود ندارد.'
        })
    
    try:
        reason = request.POST.get('reason', '').strip()
        
        with db_transaction.atomic():
            refund = transaction.create_refund(reason=reason)
            
            if refund:
                messages.success(request, 
                    f'درخواست بازگشت وجه ثبت شد. '
                    f'کد پیگیری: {refund.tracking_code}'
                )
                return JsonResponse({
                    'success': True,
                    'message': 'درخواست بازگشت وجه با موفقیت ثبت شد.',
                    'refund_id': refund.id
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'خطا در ثبت درخواست بازگشت وجه.'
                })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'خطای سیستمی رخ داده است.'
        })


@login_required
def wallet_api_balance(request):
    """API دریافت موجودی کیف پول"""
    try:
        wallet = Wallet.objects.get(user=request.user)
        return JsonResponse({
            'success': True,
            'balance': float(wallet.balance),
            'pending_balance': float(wallet.pending_balance),
            'frozen_balance': float(wallet.frozen_balance),
            'total_balance': float(wallet.get_total_balance())
        })
    except Wallet.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'کیف پول یافت نشد.'
        })


# اضافه کردن context processor helper
def get_user_balance(user):
    """دریافت موجودی کاربر برای context processor"""
    if user.is_authenticated:
        try:
            wallet = Wallet.objects.get(user=user)
            return wallet.balance
        except Wallet.DoesNotExist:
            return Decimal('0.00')
    return Decimal('0.00')
