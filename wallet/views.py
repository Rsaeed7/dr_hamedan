from decimal import Decimal

import jdatetime
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django_jalali.db import models as jmodels
from django.core.paginator import Paginator
from django.utils import timezone
from user.models import User
from .models import Wallet, Transaction, PaymentGateway
from payments.models import PaymentRequest


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
    """واریز به کیف پول - هدایت به سیستم پرداخت جدید"""
    # هدایت به سیستم پرداخت جدید
    redirect_url = reverse('payments:wallet_deposit')
    
    # اضافه کردن پارامترهای موجود
    params = []
    suggested_amount = request.GET.get('amount')
    redirect_to = request.GET.get('redirect_to')
    
    if suggested_amount:
        params.append(f'amount={suggested_amount}')
    if redirect_to:
        params.append(f'redirect_to={redirect_to}')
    
    if params:
        redirect_url += '?' + '&'.join(params)
    
    return redirect(redirect_url)


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
    """پردازش پرداخت برای رزرو - هدایت به سیستم پرداخت جدید"""
    # هدایت به سیستم پرداخت جدید
    return redirect('payments:reservation_payment', reservation_id=reservation_id)


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
