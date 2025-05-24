from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.db.models import Q, Sum, Count
from django.utils import timezone
from decimal import Decimal
import json

from .models import Discount, CouponCode, DiscountUsage, AutomaticDiscount
from reservations.models import Reservation
from user.models import User


class DiscountListView(ListView):
    """لیست تخفیفات عمومی"""
    model = Discount
    template_name = 'discounts/discount_list.html'
    context_object_name = 'discounts'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Discount.objects.filter(
            status='active',
            is_public=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).select_related('discount_type')
        
        # فیلتر بر اساس نوع تخفیف
        discount_type = self.request.GET.get('type')
        if discount_type:
            queryset = queryset.filter(discount_type__type=discount_type)
        
        # فیلتر بر اساس تخصص
        specialization = self.request.GET.get('specialization')
        if specialization:
            queryset = queryset.filter(
                Q(applicable_to='all') | 
                Q(applicable_to='specialization', specializations__id=specialization)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['discount_types'] = [
            ('percentage', 'درصدی'),
            ('fixed_amount', 'مبلغ ثابت'),
        ]
        return context


class DiscountDetailView(DetailView):
    """جزئیات تخفیف"""
    model = Discount
    template_name = 'discounts/discount_detail.html'
    context_object_name = 'discount'
    
    def get_queryset(self):
        return Discount.objects.filter(
            status='active',
            is_public=True
        ).select_related('discount_type')


@login_required
def apply_coupon_code(request):
    """اعمال کد تخفیف"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'روش نامعتبر'})
    
    try:
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code', '').strip().upper()
        reservation_id = data.get('reservation_id')
        
        if not coupon_code:
            return JsonResponse({'success': False, 'message': 'کد تخفیف وارد نشده'})
        
        if not reservation_id:
            return JsonResponse({'success': False, 'message': 'شناسه رزرو نامعتبر'})
        
        # یافتن کد تخفیف
        try:
            coupon = CouponCode.objects.get(code=coupon_code, is_active=True)
        except CouponCode.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'کد تخفیف نامعتبر'})
        
        # بررسی معتبر بودن کد تخفیف
        if not coupon.is_valid():
            return JsonResponse({'success': False, 'message': 'کد تخفیف منقضی شده'})
        
        # یافتن رزرو
        try:
            reservation = Reservation.objects.get(
                id=reservation_id,
                patient__user=request.user,
                status='pending'
            )
        except Reservation.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'رزرو یافت نشد'})
        
        # بررسی اینکه آیا قبلاً تخفیف اعمال شده
        if hasattr(reservation, 'discount_usage'):
            return JsonResponse({'success': False, 'message': 'قبلاً تخفیف اعمال شده'})
        
        # اعمال تخفیف
        success, message = coupon.discount.apply_to_reservation(reservation, request.user)
        
        if success:
            # بروزرسانی کد تخفیف در رکورد استفاده
            discount_usage = reservation.discount_usage
            discount_usage.coupon_code = coupon
            discount_usage.save()
            
            # بروزرسانی مبلغ رزرو
            reservation.amount = discount_usage.final_amount
            reservation.save()
            
            return JsonResponse({
                'success': True,
                'message': message,
                'discount_amount': float(discount_usage.discount_amount),
                'final_amount': float(discount_usage.final_amount),
                'original_amount': float(discount_usage.original_amount)
            })
        else:
            return JsonResponse({'success': False, 'message': message})
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'داده‌های نامعتبر'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'خطای سیستم'})


@login_required
def check_automatic_discounts(request):
    """بررسی تخفیفات خودکار"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'روش نامعتبر'})
    
    try:
        data = json.loads(request.body)
        reservation_id = data.get('reservation_id')
        
        if not reservation_id:
            return JsonResponse({'success': False, 'message': 'شناسه رزرو نامعتبر'})
        
        # یافتن رزرو
        try:
            reservation = Reservation.objects.get(
                id=reservation_id,
                patient__user=request.user,
                status='pending'
            )
        except Reservation.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'رزرو یافت نشد'})
        
        # بررسی اینکه آیا قبلاً تخفیف اعمال شده
        if hasattr(reservation, 'discount_usage'):
            return JsonResponse({'success': False, 'message': 'قبلاً تخفیف اعمال شده'})
        
        # بررسی تخفیفات خودکار
        automatic_discounts = AutomaticDiscount.objects.filter(
            is_active=True,
            discount__status='active'
        ).select_related('discount')
        
        applied_discount = None
        for auto_discount in automatic_discounts:
            if auto_discount.check_conditions(reservation, request.user):
                success, message = auto_discount.discount.apply_to_reservation(reservation, request.user)
                if success:
                    applied_discount = auto_discount.discount
                    break
        
        if applied_discount:
            discount_usage = reservation.discount_usage
            reservation.amount = discount_usage.final_amount
            reservation.save()
            
            return JsonResponse({
                'success': True,
                'message': f'تخفیف خودکار "{applied_discount.title}" اعمال شد',
                'discount_amount': float(discount_usage.discount_amount),
                'final_amount': float(discount_usage.final_amount),
                'original_amount': float(discount_usage.original_amount),
                'discount_title': applied_discount.title
            })
        else:
            return JsonResponse({'success': False, 'message': 'تخفیف خودکاری یافت نشد'})
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'داده‌های نامعتبر'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'خطای سیستم'})


@login_required
def get_available_discounts(request):
    """دریافت تخفیفات قابل اعمال برای کاربر"""
    try:
        reservation_id = request.GET.get('reservation_id')
        
        if not reservation_id:
            return JsonResponse({'success': False, 'message': 'شناسه رزرو نامعتبر'})
        
        # یافتن رزرو
        try:
            reservation = Reservation.objects.get(
                id=reservation_id,
                patient__user=request.user,
                status='pending'
            )
        except Reservation.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'رزرو یافت نشد'})
        
        # یافتن تخفیفات قابل اعمال
        available_discounts = []
        discounts = Discount.objects.filter(
            status='active',
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).select_related('discount_type')
        
        for discount in discounts:
            if discount.can_be_used_by_user(request.user) and discount._is_applicable_to_reservation(reservation):
                discount_amount = discount.calculate_discount(reservation.amount)
                if discount_amount > 0:
                    available_discounts.append({
                        'id': discount.id,
                        'title': discount.title,
                        'description': discount.description,
                        'discount_amount': float(discount_amount),
                        'discount_type': discount.discount_type.get_type_display(),
                        'has_coupon_codes': discount.coupon_codes.filter(is_active=True).exists()
                    })
        
        return JsonResponse({
            'success': True,
            'discounts': available_discounts
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'خطای سیستم'})


@login_required
def remove_discount(request):
    """حذف تخفیف از رزرو"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'روش نامعتبر'})
    
    try:
        data = json.loads(request.body)
        reservation_id = data.get('reservation_id')
        
        if not reservation_id:
            return JsonResponse({'success': False, 'message': 'شناسه رزرو نامعتبر'})
        
        # یافتن رزرو
        try:
            reservation = Reservation.objects.get(
                id=reservation_id,
                patient__user=request.user,
                status='pending'
            )
        except Reservation.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'رزرو یافت نشد'})
        
        # بررسی وجود تخفیف
        if not hasattr(reservation, 'discount_usage'):
            return JsonResponse({'success': False, 'message': 'تخفیفی اعمال نشده'})
        
        # حذف تخفیف
        discount_usage = reservation.discount_usage
        original_amount = discount_usage.original_amount
        
        # کاهش تعداد استفاده از تخفیف
        discount = discount_usage.discount
        discount.used_count = max(0, discount.used_count - 1)
        discount.save()
        
        # حذف رکورد استفاده
        discount_usage.delete()
        
        # بازگردانی مبلغ اصلی
        reservation.amount = original_amount
        reservation.save()
        
        return JsonResponse({
            'success': True,
            'message': 'تخفیف حذف شد',
            'original_amount': float(original_amount)
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'داده‌های نامعتبر'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'خطای سیستم'})


@login_required
def user_discount_history(request):
    """تاریخچه استفاده از تخفیفات کاربر"""
    discount_usages = DiscountUsage.objects.filter(
        user=request.user
    ).select_related('discount', 'reservation', 'coupon_code').order_by('-used_at')
    
    context = {
        'discount_usages': discount_usages,
        'total_saved': discount_usages.aggregate(
            total=Sum('discount_amount')
        )['total'] or Decimal('0')
    }
    
    return render(request, 'discounts/user_discount_history.html', context)


def validate_coupon_code(request):
    """اعتبارسنجی کد تخفیف (بدون اعمال)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'روش نامعتبر'})
    
    try:
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code', '').strip().upper()
        
        if not coupon_code:
            return JsonResponse({'success': False, 'message': 'کد تخفیف وارد نشده'})
        
        # یافتن کد تخفیف
        try:
            coupon = CouponCode.objects.get(code=coupon_code, is_active=True)
        except CouponCode.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'کد تخفیف نامعتبر'})
        
        # بررسی معتبر بودن
        if not coupon.is_valid():
            return JsonResponse({'success': False, 'message': 'کد تخفیف منقضی شده'})
        
        discount = coupon.discount
        
        return JsonResponse({
            'success': True,
            'message': 'کد تخفیف معتبر است',
            'discount': {
                'title': discount.title,
                'description': discount.description,
                'type': discount.discount_type.get_type_display(),
                'percentage': float(discount.percentage) if discount.percentage else None,
                'fixed_amount': float(discount.fixed_amount) if discount.fixed_amount else None,
                'min_amount': float(discount.min_amount) if discount.min_amount else None,
                'max_discount_amount': float(discount.max_discount_amount) if discount.max_discount_amount else None
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'داده‌های نامعتبر'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'خطای سیستم'}) 