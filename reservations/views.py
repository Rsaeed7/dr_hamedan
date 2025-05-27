from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
from .models import Reservation, ReservationDay
from doctors.models import Doctor
from patients.models import PatientsFile
# from datetime import datetime
# from datetime import timedelta
import jdatetime
from jdatetime import datetime
from jdatetime import timedelta
from .services import BookingService, AppointmentService


@login_required
def book_appointment(request, doctor_id):
    """Handle booking a new appointment"""
    doctor = get_object_or_404(Doctor, id=doctor_id, is_available=True)

    if request.method == 'POST':
        # Process form data
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        national_id = request.POST.get('national_id', '')
        email = request.POST.get('email', '')
        notes = request.POST.get('notes', '')

        if date_str and time_str and name and phone:
            try:
                # Parse date
                date_parts = date_str.split('-')
                booking_date = datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2])).date()

                # Parse time
                booking_time = datetime.strptime(time_str, '%H:%M').time()

                # Prepare patient data
                patient_data = {
                    'name': name,
                    'phone': phone,
                    'national_id': national_id,
                    'email': email,
                    'notes': notes
                }

                # Use booking service to create reservation
                reservation, error_message = BookingService.create_reservation(
                    doctor=doctor,
                    date=booking_date,
                    time=booking_time,
                    patient_data=patient_data,
                    user=request.user if request.user.is_authenticated else None
                )

                if reservation:
                    messages.success(request, "رزرو با موفقیت ایجاد شد. لطفا پرداخت را تکمیل کنید.")
                    # Redirect to payment page
                    return redirect('wallet:process_payment', reservation_id=reservation.id)
                else:
                    messages.error(request, error_message)
                    
            except Exception as e:
                messages.error(request, f"خطا در پردازش درخواست: {str(e)}")
        else:
            messages.error(request, "لطفا تمام فیلدهای الزامی را تکمیل کنید.")

    # Get available dates and slots for this doctor using service
    available_days = BookingService.get_available_days_for_doctor(doctor, days_ahead=7)

    context = {
        'doctor': doctor,
        'available_days': available_days,
    }

    return render(request, 'reservations/appointment_book.html', context)

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
