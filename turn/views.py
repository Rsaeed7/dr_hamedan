from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from jdatetime import date, timedelta
from decimal import Decimal

from turn.utils.turn_maker import create_reservations
from .models import Reservation_Day, Reservation, Patients_File
from .forms import ReservationForm
from doctors.models import Doctor
from wallet.models import Wallet, InsufficientFunds
import re


def turn(request):
    today = date.today()
    cutoff_date = today + timedelta(days=90)
    reservations_Day = Reservation_Day.objects.filter(published=True, date__lte=cutoff_date)
    
    # Get available doctors
    doctors = Doctor.objects.filter(is_available=True)
    selected_doctor_id = request.GET.get('doctor')
    
    if selected_doctor_id:
        selected_doctor = get_object_or_404(Doctor, id=selected_doctor_id)
    else:
        selected_doctor = None
    
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            id = request.POST.get('id')
            doctor_id = request.POST.get('doctor')
            name = re.sub(' +', ' ', cd['name'])
            
            # Get the reservation and doctor
            reservation = Reservation.objects.get(id=id)
            doctor = get_object_or_404(Doctor, id=doctor_id)
            
            # Set the reservation amount to the doctor's consultation fee
            amount = doctor.consultation_fee
            
            # Create or get the patient
            if Patients_File.objects.filter(name=name, meli_code=cd['meli_code']):
                patient = Patients_File.objects.get(name=name, meli_code=cd['meli_code'])
            else:
                patient = Patients_File.objects.create(
                    name=name,
                    phone=cd['phone'],
                    meli_code=cd['meli_code'],
                    involvement=cd.get('involvement', '')
                )
                
            # Update the reservation with patient, doctor, amount
            reservation.patient = patient
            reservation.doctor = doctor
            reservation.phone = cd['phone']
            reservation.amount = amount
            reservation.save()
            
            # If user is logged in, attempt automatic payment
            if request.user.is_authenticated:
                try:
                    # Redirect to payment confirmation page
                    return redirect('turn:payment_confirmation', reservation_id=reservation.id)
                except:
                    pass
            
            # For guest users or if wallet payment failed
            message = f"{name} عزیز نوبت شما با دکتر {doctor} در تاریخ {reservation.day} و ساعت {reservation.time} ثبت شد. لطفا نسبت به پرداخت هزینه ویزیت اقدام نمایید."
            messages.success(request, message)
            return redirect('turn:payment_redirect', reservation_id=reservation.id)
        else:
            messages.error(request, "لطفا اطلاعات را به درستی وارد کنید")
            return redirect('turn:turn_days')
    else:
        form = ReservationForm()
    
    context = {
        'reservations_Day': reservations_Day,
        'form': form,
        'today': today,
        'doctors': doctors,
        'selected_doctor': selected_doctor
    }
    return render(request, 'turn/turn.html', context)


@login_required
def payment_confirmation(request, reservation_id):
    """Confirm and process payment from wallet"""
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    # Ensure reservation belongs to current user
    if hasattr(request.user, 'patient_profile') and request.user.patient_profile == reservation.patient:
        pass
    else:
        messages.error(request, "شما اجازه دسترسی به این نوبت را ندارید")
        return redirect('turn:turn_days')
    
    # Get or create user wallet
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Check sufficient funds and make payment
                if wallet.balance < reservation.amount:
                    raise InsufficientFunds("موجودی کیف پول کافی نیست")
                
                # Process the payment
                wallet.make_payment(reservation.amount)
                
                # Update the reservation status
                reservation.payment_status = Reservation.PAYMENT_PAID
                reservation.status = Reservation.STATUS_CONFIRMED
                reservation.save()
                
                messages.success(request, f"پرداخت با موفقیت انجام شد. نوبت شما با دکتر {reservation.doctor} تایید شد.")
                return redirect('turn:confirm')
                
        except InsufficientFunds:
            messages.error(request, "موجودی کیف پول شما کافی نیست. لطفا نسبت به شارژ کیف پول اقدام نمایید.")
            return redirect('wallet:deposit')
    
    context = {
        'reservation': reservation,
        'wallet': wallet
    }
    return render(request, 'turn/payment_confirmation.html', context)


def payment_redirect(request, reservation_id):
    """Redirect to appropriate payment method"""
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    # Check if user is logged in
    if request.user.is_authenticated:
        # Direct to wallet payment
        return redirect('turn:payment_confirmation', reservation_id=reservation.id)
    else:
        # For guest users, show payment options or direct to payment gateway
        context = {
            'reservation': reservation
        }
        return render(request, 'turn/payment_options.html', context)


def turn_maker(request):
    if request.user.is_authenticated and request.user.is_staff:
        create_reservations()
        return HttpResponse('نوبت ها تا یک سال آینده ساخته شدند لطفا روزهای تعطیل رسمی و تعطیلی های مطب را به حالت نوبت غیر فعال تغییر دهید')
    else:
        return HttpResponse('ابتدا وارد حساب کاربری مدیر خود شوید')


def confirm(request):
    return render(request, 'turn/confirm.html')


def get_doctor_slots(request, doctor_id, date_id):
    """AJAX endpoint to get available slots for a doctor on a specific date"""
    doctor = get_object_or_404(Doctor, id=doctor_id)
    day = get_object_or_404(Reservation_Day, id=date_id)
    
    # Get doctor's existing reservations for this day
    existing_reservations = Reservation.objects.filter(doctor=doctor, day=day)
    booked_times = [r.time.strftime('%H:%M') for r in existing_reservations]
    
    # Get available slots based on doctor's availability
    # This is a simplified example - actual implementation would need to consider doctor's availability schedule
    all_slots = ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00', 
                 '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00']
    
    available_slots = [slot for slot in all_slots if slot not in booked_times]
    
    return JsonResponse({
        'available_slots': available_slots,
        'doctor_name': str(doctor),
        'consultation_fee': float(doctor.consultation_fee)
    })
