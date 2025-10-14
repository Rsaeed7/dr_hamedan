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
from django.urls import reverse
from user.models import User
from doctors.models import Doctor
from patients.models import PatientsFile
from .models import Reservation, ReservationDay
from wallet.models import Wallet, Transaction
from payments.models import PaymentRequest
from datetime import datetime
from datetime import timedelta
import jdatetime
from jdatetime import datetime
from jdatetime import timedelta
from .services import BookingService, AppointmentService
import logging

logger = logging.getLogger(__name__)


@login_required
def book_appointment(request, doctor_slug):  # تغییر از doctor_id به doctor_slug
    """نمایش فرم رزرو نوبت و پردازش درخواست رزرو"""
    if not request.user.is_authenticated:
        messages.error(request, 'برای رزرو نوبت باید وارد شوید')
        return redirect('user:login')

    try:
        doctor = Doctor.objects.get(slug=doctor_slug, is_available=True)  # تغییر به slug
    except Doctor.DoesNotExist:
        messages.error(request, 'پزشک مورد نظر یافت نشد یا غیرفعال است')
        return redirect('doctors:doctor_list')

    booking_service = BookingService()

    if request.method == 'POST':
        try:
            user = request.user
            date_str = request.POST.get('date')
            time_str = request.POST.get('time')
            patient_name = request.POST.get('patient_name', '').strip()
            patient_last_name = request.POST.get('patient_last_name', '').strip()
            patient_national_id = request.POST.get('patient_national_id', '').strip()
            patient_email = request.POST.get('patient_email', '').strip()

            if not all([date_str, time_str]):
                messages.error(request, 'لطفاً تاریخ و ساعت را انتخاب کنید')
                return redirect('reservations:book_appointment', doctor_slug=doctor_slug)  # تغییر به slug

            # تبدیل تاریخ جلالی به میلادی
            try:
                jalali_date = jdatetime.date(*map(int, date_str.split('/')))
                gregorian_date = jalali_date.togregorian()
            except (ValueError, TypeError):
                messages.error(request, 'فرمت تاریخ نامعتبر است')
                return redirect('reservations:book_appointment', doctor_slug=doctor_slug)  # تغییر به slug

            # تبدیل ساعت
            try:
                appointment_time = datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                messages.error(request, 'فرمت ساعت نامعتبر است')
                return redirect('reservations:book_appointment', doctor_slug=doctor_slug)  # تغییر به slug

            # یافتن رزرو موجود
            try:
                reservation_day = ReservationDay.objects.get(
                    date=gregorian_date,
                    published=True
                )

                reservation = Reservation.objects.get(
                    doctor=doctor,
                    day=reservation_day,
                    time=appointment_time,
                    status='available'
                )
            except ReservationDay.DoesNotExist:
                messages.error(request, 'تاریخ انتخابی برای رزرو در دسترس نیست')
                return redirect('reservations:book_appointment', doctor_slug=doctor_slug)  # تغییر به slug
            except Reservation.DoesNotExist:
                messages.error(request, 'ساعت انتخابی برای رزرو در دسترس نیست')
                return redirect('reservations:book_appointment', doctor_slug=doctor_slug)  # تغییر به slug

            # رزرو نوبت
            patient_data = {
                'name': patient_name + ' ' + patient_last_name,
                'phone': request.POST.get('phone', user.phone if hasattr(user, 'phone') else ''),
                'national_id': patient_national_id,
                'email': patient_email
            }

            # Check payment method preference
            payment_method = request.POST.get('payment_method', 'wallet')

            if payment_method == 'direct':
                # CRITICAL FIX: For direct payment, DON'T lock the reservation yet
                # Store booking intent in session and only lock after payment success
                
                # Store all booking data in session
                request.session['pending_direct_booking'] = {
                    'doctor_slug': doctor_slug,
                    'doctor_id': doctor.id,
                    'reservation_id': reservation.id,
                    'date': date_str,
                    'time': time_str,
                    'patient_data': patient_data,
                    'appointment_time': appointment_time.strftime('%H:%M'),
                    'gregorian_date': gregorian_date.strftime('%Y-%m-%d'),
                }
                
                # Redirect to payment WITHOUT locking the reservation
                return redirect('payments:reservation_payment', reservation_id=reservation.id)
            else:
                # Wallet payment booking
                success, message = reservation.book_appointment(
                    patient_data=patient_data,
                    user=request.user
                )

                user.first_name = patient_name
                user.last_name = patient_last_name
                user.patient.national_id = patient_national_id
                user.patient.save()
                user.save()

                if success:
                    messages.success(request, message)
                    return redirect('reservations:view_appointment', pk=reservation.id)
                else:
                    messages.error(request, message)
                    if "موجودی کیف پول کافی نیست" in message:
                        # Store form data in session for payment choice
                        request.session['pending_booking_data'] = {
                            'doctor_slug': doctor_slug,  # تغییر به slug
                            'date': date_str,
                            'time': time_str,
                            'patient_data': patient_data,
                            'reservation_id': reservation.id
                        }

                        # Redirect to payment choice page
                        return redirect('reservations:payment_choice', reservation_id=reservation.id)
                    return redirect('reservations:book_appointment', doctor_slug=doctor_slug)  # تغییر به slug

        except Exception as e:
            logger.error(f"خطا در رزرو نوبت: {str(e)}")
            messages.error(request, 'خطایی در رزرو نوبت رخ داد. لطفاً دوباره تلاش کنید')
            return redirect('reservations:book_appointment', doctor_slug=doctor_slug)  # تغییر به slug

    # GET request - نمایش فرم
    try:
        # دریافت روزهای موجود (30 روز آینده)
        available_days = booking_service.get_available_days_for_doctor(doctor.id,
                                                                       days_ahead=30)  # همچنان از id داخلی استفاده کن

        # Extract year and month from first available day for JavaScript initialization
        initial_year = None
        initial_month = None
        if available_days:
            first_day = available_days[0]
            if 'jalali_date_str' in first_day:
                date_parts = first_day['jalali_date_str'].split('/')
                if len(date_parts) == 3:
                    initial_year = int(date_parts[0])
                    initial_month = int(date_parts[1])

        # Get user's wallet balance and patient info
        wallet_balance = 0
        patient_info = {
            'national_id': '',
            'email': request.user.email or '',
        }

        if request.user.is_authenticated:
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            wallet_balance = wallet.balance

            # Get patient file info if exists
            try:
                patient_file = PatientsFile.objects.get(user=request.user)
                patient_info['national_id'] = patient_file.national_id or ''
                if patient_file.email:
                    patient_info['email'] = patient_file.email
            except PatientsFile.DoesNotExist:
                pass

        context = {
            'doctor': doctor,
            'days': available_days,
            'initial_year': initial_year,
            'initial_month': initial_month,
            'balance': wallet_balance,
            'patient_info': patient_info,
        }

        return render(request, 'reservations/appointment_book.html', context)

    except Exception as e:
        logger.error(f"خطا در دریافت روزهای موجود: {str(e)}")
        messages.error(request, 'خطایی در بارگذاری اطلاعات رخ داد')
        return redirect('doctors:doctor_detail', slug=doctor_slug)  # تغییر به slug


@login_required
def ajax_get_month_availability(request, doctor_slug):  # تغییر به slug
    """AJAX endpoint for getting availability for a specific month"""
    if request.method != 'GET':
        return JsonResponse({'error': 'فقط درخواست GET مجاز است'}, status=405)

    try:
        jalali_year = int(request.GET.get('year'))
        jalali_month = int(request.GET.get('month'))

        if not (1 <= jalali_month <= 12):
            return JsonResponse({'error': 'ماه نامعتبر است'}, status=400)

        # ابتدا پزشک رو با slug پیدا کن
        doctor = get_object_or_404(Doctor, slug=doctor_slug)

        booking_service = BookingService()
        available_days = booking_service.get_available_days_for_month(
            doctor.id, jalali_year, jalali_month  # همچنان از id داخلی استفاده کن
        )

        return JsonResponse({
            'success': True,
            'available_days': available_days,
            'year': jalali_year,
            'month': jalali_month
        })

    except (ValueError, TypeError):
        return JsonResponse({'error': 'پارامترهای نامعتبر'}, status=400)
    except Exception as e:
        logger.error(f"خطا در دریافت اطلاعات ماه: {str(e)}")
        return JsonResponse({'error': 'خطای سرور'}, status=500)


@login_required
def ajax_get_day_slots(request, doctor_slug):  # تغییر به slug
    """AJAX endpoint for getting slots for a specific day"""
    if request.method != 'GET':
        return JsonResponse({'error': 'فقط درخواست GET مجاز است'}, status=405)

    try:
        jalali_date_str = request.GET.get('date')

        if not jalali_date_str:
            return JsonResponse({'error': 'تاریخ مشخص نشده'}, status=400)

        # ابتدا پزشک رو با slug پیدا کن
        doctor = get_object_or_404(Doctor, slug=doctor_slug)

        booking_service = BookingService()
        slots = booking_service.get_day_slots(doctor.id, jalali_date_str)  # همچنان از id داخلی استفاده کن

        return JsonResponse({
            'success': True,
            'slots': slots,
            'date': jalali_date_str
        })

    except Exception as e:
        logger.error(f"خطا در دریافت اسلات‌های روز: {str(e)}")
        return JsonResponse({'error': 'خطای سرور'}, status=500)


# سایر ویوها بدون تغییر می‌مانند چون از reservation_id استفاده می‌کنند
@login_required
def payment_choice(request, reservation_id):
    """انتخاب روش پرداخت برای رزرو نوبت"""
    try:
        reservation = Reservation.objects.get(
            id=reservation_id,
            status='available',
            payment_status='pending'
        )
    except Reservation.DoesNotExist:
        messages.error(request, 'رزرو مورد نظر یافت نشد')
        return redirect('home')

    # Get user's wallet
    from wallet.models import Wallet
    wallet, created = Wallet.objects.get_or_create(user=request.user)

    # Calculate amounts
    required_amount = reservation.amount
    current_balance = wallet.balance
    needed_amount = max(0, required_amount - current_balance)

    # Calculate suggested deposit amount
    suggested_amount = int(needed_amount * 1.1)
    suggested_amount = ((suggested_amount + 9999) // 10000) * 10000
    suggested_amount = max(10000, suggested_amount)

    context = {
        'reservation': reservation,
        'wallet': wallet,
        'required_amount': required_amount,
        'current_balance': current_balance,
        'needed_amount': needed_amount,
        'suggested_amount': suggested_amount,
    }

    return render(request, 'reservations/payment_choice.html', context)


@login_required
def process_payment_choice(request, reservation_id):
    """پردازش انتخاب روش پرداخت"""
    if request.method != 'POST':
        return redirect('reservations:payment_choice', reservation_id=reservation_id)

    payment_choice = request.POST.get('payment_choice')

    if payment_choice == 'wallet_charge':
        # Redirect to wallet deposit
        suggested_amount = request.POST.get('suggested_amount', '10000')
        return redirect(
            f"{reverse('wallet:deposit')}?amount={suggested_amount}&redirect_to={reverse('reservations:payment_choice', args=[reservation_id])}")

    elif payment_choice == 'direct_payment':
        # Get pending booking data from session
        pending_data = request.session.get('pending_booking_data', {})

        if not pending_data or pending_data.get('reservation_id') != reservation_id:
            messages.error(request, 'اطلاعات رزرو یافت نشد. لطفاً دوباره تلاش کنید.')
            return redirect('reservations:book_appointment',
                            doctor_slug=pending_data.get('doctor_slug', 'default-doctor'))  # تغییر به slug

        try:
            reservation = Reservation.objects.get(id=reservation_id)

            # Book with direct payment
            success, message = reservation.book_with_direct_payment(
                patient_data=pending_data['patient_data'],
                user=request.user
            )

            if success:
                # Clear session data
                if 'pending_booking_data' in request.session:
                    del request.session['pending_booking_data']

                # Redirect to payment page
                return redirect('payments:reservation_payment', reservation_id=reservation.id)
            else:
                messages.error(request, message)
                return redirect('reservations:payment_choice', reservation_id=reservation_id)

        except Reservation.DoesNotExist:
            messages.error(request, 'رزرو مورد نظر یافت نشد')
            return redirect('home')

    else:
        messages.error(request, 'انتخاب نامعتبر')
        return redirect('reservations:payment_choice', reservation_id=reservation_id)

@login_required
def confirm_appointment(request, pk):
    """Confirm a pending appointment"""
    # Get the reservation
    reservation = get_object_or_404(Reservation, pk=pk)
    
    # Check permissions (doctor or clinic admin)
    is_authorized = False
    
    if hasattr(request.user, 'doctor') and request.user.doctor == reservation.doctor:
        is_authorized = True
    elif hasattr(reservation.doctor, 'clinic') and reservation.doctor.clinic and reservation.doctor.clinic.admin == request.user:
        is_authorized = True
    
    if not is_authorized:
        messages.error(request, "شما مجوز تایید این نوبت را ندارید.")
        return redirect('home')
    
    # Use appointment service to confirm
    success, message = AppointmentService.confirm_appointment(
        reservation, 
        confirmed_by=request.user
    )
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    # Redirect back to appointments list
    if hasattr(request.user, 'doctor'):
        return redirect('doctors:doctor_appointments')
    else:
        return redirect('clinics:clinic_appointments')

@login_required
def cancel_appointment(request, pk):
    """Cancel an appointment"""
    # Get the reservation
    reservation = get_object_or_404(Reservation, pk=pk)
    
    # Check permissions (doctor, clinic admin, or the patient)
    is_authorized = False
    
    if hasattr(request.user, 'doctor') and request.user.doctor == reservation.doctor:
        is_authorized = True
    elif hasattr(reservation.doctor, 'clinic') and reservation.doctor.clinic and reservation.doctor.clinic.admin == request.user:
        is_authorized = True
    elif reservation.patient and reservation.patient.user == request.user:
        is_authorized = True
    
    if not is_authorized:
        messages.error(request, "شما مجوز لغو این نوبت را ندارید.")
        return redirect('home')
    
    # Process cancellation with refund
    refund = request.GET.get('refund', 'true').lower() == 'true'
    
    success, message = AppointmentService.cancel_appointment(
        reservation,
        cancelled_by=request.user,
        refund=refund
    )
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    # Redirect based on user type
    if hasattr(request.user, 'doctor'):
        return redirect('doctors:doctor_appointments')
    elif reservation.doctor.clinic and reservation.doctor.clinic.admin == request.user:
        return redirect('clinics:clinic_appointments')
    else:
        return redirect('patients:patient_appointments')

@login_required
def complete_appointment(request, pk):
    """Mark an appointment as completed"""
    # Get the reservation
    reservation = get_object_or_404(Reservation, pk=pk)
    
    # Check permissions (doctor or clinic admin)
    is_authorized = False
    
    if hasattr(request.user, 'doctor') and request.user.doctor == reservation.doctor:
        is_authorized = True
    elif hasattr(reservation.doctor, 'clinic') and reservation.doctor.clinic and reservation.doctor.clinic.admin == request.user:
        is_authorized = True
    
    if not is_authorized:
        messages.error(request, "شما مجوز تکمیل این نوبت را ندارید.")
        return redirect('home')
    
    # Use appointment service to complete
    success, message = AppointmentService.complete_appointment(
        reservation,
        completed_by=request.user
    )
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    # Redirect based on user type
    if hasattr(request.user, 'doctor'):
        return redirect('doctors:doctor_appointments')
    else:
        return redirect('clinics:clinic_appointments')

def appointment_status(request, pk):
    """Check the status of an appointment"""
    reservation = get_object_or_404(Reservation, pk=pk)
    
    # Anyone with the appointment ID can check status
    context = {
        'reservation': reservation,
        'doctor': reservation.doctor,
    }
    
    return render(request, 'reservations/status_appointment.html', context)

@login_required
def manage_reservation_days(request):
    """Manage which days are published for reservations"""
    # Only admin users should access this
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "You don't have permission to manage reservation days.")
        return redirect('home')
    
    if request.method == 'POST':
        # Process form submission
        day_id = request.POST.get('day_id')
        action = request.POST.get('action')
        
        if day_id and action:
            day = get_object_or_404(ReservationDay, id=day_id)
            
            if action == 'publish':
                day.published = True
            elif action == 'unpublish':
                day.published = False
            
            day.save()
            
            return JsonResponse({'status': 'success'})
    
    # Get all reservation days for the next 30 days
    today = datetime.now().date()
    days = []
    
    for i in range(30):
        day = today.replace(day=today.day + i)
        reservation_day, created = ReservationDay.objects.get_or_create(date=day)
        days.append(reservation_day)
    
    context = {
        'days': days,
    }
    
    return render(request, 'reservations/manage_days.html', context)

@login_required
def view_appointment(request, pk):
    """View details of a specific appointment"""
    appointment = get_object_or_404(Reservation, pk=pk)
    
    # Check if the user is authorized to view this appointment
    if request.user.is_admin or request.user.is_superuser:
        # Admin can view any appointment
        pass
    elif hasattr(request.user, 'doctor') and appointment.doctor.user == request.user:
        # Doctor can view their own appointments
        pass
    elif hasattr(request.user, 'patient') and appointment.patient.user == request.user:
        # Patient can view their own appointments
        pass
    else:
        messages.error(request, "You don't have permission to view this appointment.")
        return redirect('doctors:doctor_list')
    
    context = {
        'appointment': appointment,
    }
    
    return render(request, 'reservations/appointment_view.html', context)

@login_required
def ajax_get_month_availability(request, doctor_id):
    """AJAX endpoint for getting availability for a specific month"""
    if request.method != 'GET':
        return JsonResponse({'error': 'فقط درخواست GET مجاز است'}, status=405)
    
    try:
        jalali_year = int(request.GET.get('year'))
        jalali_month = int(request.GET.get('month'))
        
        if not (1 <= jalali_month <= 12):
            return JsonResponse({'error': 'ماه نامعتبر است'}, status=400)
        
        booking_service = BookingService()
        available_days = booking_service.get_available_days_for_month(
            doctor_id, jalali_year, jalali_month
        )
        
        return JsonResponse({
            'success': True,
            'available_days': available_days,
            'year': jalali_year,
            'month': jalali_month
        })
        
    except (ValueError, TypeError):
        return JsonResponse({'error': 'پارامترهای نامعتبر'}, status=400)
    except Exception as e:
        logger.error(f"خطا در دریافت اطلاعات ماه: {str(e)}")
        return JsonResponse({'error': 'خطای سرور'}, status=500)

@login_required
def ajax_get_day_slots(request, doctor_id):
    """AJAX endpoint for getting slots for a specific day"""
    if request.method != 'GET':
        return JsonResponse({'error': 'فقط درخواست GET مجاز است'}, status=405)
    
    try:
        jalali_date_str = request.GET.get('date')
        
        if not jalali_date_str:
            return JsonResponse({'error': 'تاریخ مشخص نشده'}, status=400)
        
        booking_service = BookingService()
        slots = booking_service.get_day_slots(doctor_id, jalali_date_str)
        
        return JsonResponse({
            'success': True,
            'slots': slots,
            'date': jalali_date_str
        })
        
    except Exception as e:
        logger.error(f"خطا در دریافت اسلات‌های روز: {str(e)}")
        return JsonResponse({'error': 'خطای سرور'}, status=500)

@login_required
def payment_choice(request, reservation_id):
    """انتخاب روش پرداخت برای رزرو نوبت"""
    try:
        reservation = Reservation.objects.get(
            id=reservation_id,
            status='available',
            payment_status='pending'
        )
    except Reservation.DoesNotExist:
        messages.error(request, 'رزرو مورد نظر یافت نشد')
        return redirect('home')
    
    # Get user's wallet
    from wallet.models import Wallet
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Calculate amounts
    required_amount = reservation.amount
    current_balance = wallet.balance
    needed_amount = max(0, required_amount - current_balance)
    
    # Calculate suggested deposit amount
    suggested_amount = int(needed_amount * 1.1)
    suggested_amount = ((suggested_amount + 9999) // 10000) * 10000
    suggested_amount = max(10000, suggested_amount)
    
    context = {
        'reservation': reservation,
        'wallet': wallet,
        'required_amount': required_amount,
        'current_balance': current_balance,
        'needed_amount': needed_amount,
        'suggested_amount': suggested_amount,
    }
    
    return render(request, 'reservations/payment_choice.html', context)


@login_required
def process_payment_choice(request, reservation_id):
    """پردازش انتخاب روش پرداخت"""
    if request.method != 'POST':
        return redirect('reservations:payment_choice', reservation_id=reservation_id)
    
    payment_choice = request.POST.get('payment_choice')
    
    if payment_choice == 'wallet_charge':
        # Redirect to wallet deposit
        suggested_amount = request.POST.get('suggested_amount', '10000')
        return redirect(f"{reverse('wallet:deposit')}?amount={suggested_amount}&redirect_to={reverse('reservations:payment_choice', args=[reservation_id])}")
    
    elif payment_choice == 'direct_payment':
        # Get pending booking data from session
        pending_data = request.session.get('pending_booking_data', {})
        
        if not pending_data or pending_data.get('reservation_id') != reservation_id:
            messages.error(request, 'اطلاعات رزرو یافت نشد. لطفاً دوباره تلاش کنید.')
            return redirect('reservations:book_appointment', doctor_id=pending_data.get('doctor_id', 1))
        
        try:
            reservation = Reservation.objects.get(id=reservation_id)
            
            # Book with direct payment
            success, message = reservation.book_with_direct_payment(
                patient_data=pending_data['patient_data'],
                user=request.user
            )
            
            if success:
                # Clear session data
                if 'pending_booking_data' in request.session:
                    del request.session['pending_booking_data']
                
                # Redirect to payment page
                return redirect('payments:reservation_payment', reservation_id=reservation.id)
            else:
                messages.error(request, message)
                return redirect('reservations:payment_choice', reservation_id=reservation_id)
                
        except Reservation.DoesNotExist:
            messages.error(request, 'رزرو مورد نظر یافت نشد')
            return redirect('home')
    
    else:
        messages.error(request, 'انتخاب نامعتبر')
        return redirect('reservations:payment_choice', reservation_id=reservation_id)
