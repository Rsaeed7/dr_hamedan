from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
from .models import Reservation, ReservationDay
from doctors.models import Doctor
from patients.models import PatientsFile
from datetime import datetime
from datetime import timedelta
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
        
        if date_str and time_str and name and phone:
            try:
                # Parse date
                date_parts = date_str.split('-')
                booking_date = datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2])).date()
                
                # Parse time
                time_parts = time_str.split(':')
                booking_time = datetime.strptime(time_str, '%H:%M').time()
                
                # Get or create ReservationDay
                reservation_day, _ = ReservationDay.objects.get_or_create(date=booking_date)
                
                # Check if time slot is still available
                if booking_time in doctor.get_available_slots(booking_date):
                    # Create or get patient file
                    if request.user.is_authenticated:
                        patient, created = PatientsFile.objects.get_or_create(
                            user=request.user,
                            defaults={
                                'name': name,
                                'phone': phone,
                                'national_id': national_id
                            }
                        )
                    else:
                        # For guest booking
                        patient = PatientsFile.objects.create(
                            name=name,
                            phone=phone,
                            national_id=national_id
                        )
                    
                    # Create reservation
                    reservation = Reservation.objects.create(
                        day=reservation_day,
                        patient=patient,
                        doctor=doctor,
                        time=booking_time,
                        phone=phone,
                        amount=doctor.consultation_fee,
                        status='pending',
                        payment_status='pending'
                    )
                    
                    # Redirect to payment page
                    return redirect('wallet:process_payment', reservation_id=reservation.id)
                else:
                    messages.error(request, "This time slot is no longer available. Please select another time.")
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        else:
            messages.error(request, "Please fill in all required fields.")

    # Get available dates and slots for this doctor
    days = []
    today = datetime.now().date()

    for i in range(7):
        day = today + timedelta(days=i)
        try:
            reservation_day, _ = ReservationDay.objects.get_or_create(date=day)
            if reservation_day.published:
                available_slots = doctor.get_available_slots(day)
                if available_slots:
                    days.append({
                        'date': day,
                        'slots': available_slots
                    })
        except Exception as e:
            print(f"Error processing day {day}: {e}")
    context = {
        'doctor': doctor,
        'days': days,
    }
    
    return render(request, 'reservations/book.html', context)

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
        messages.error(request, "You don't have permission to confirm this appointment.")
        return redirect('home')
    
    # Confirm the appointment
    if reservation.status == 'pending' and reservation.payment_status == 'paid':
        reservation.confirm_appointment()
        messages.success(request, "Appointment confirmed successfully.")
    else:
        messages.error(request, "Can't confirm this appointment. Check payment status.")
    
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
        messages.error(request, "You don't have permission to cancel this appointment.")
        return redirect('home')
    
    # Process cancellation with refund
    refund = request.GET.get('refund', 'true').lower() == 'true'
    
    if reservation.cancel_appointment(refund=refund):
        messages.success(request, "Appointment cancelled successfully.")
    else:
        messages.error(request, "Failed to cancel appointment.")
    
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
        messages.error(request, "You don't have permission to complete this appointment.")
        return redirect('home')
    
    # Mark as completed
    if reservation.complete_appointment():
        messages.success(request, "Appointment marked as completed.")
    else:
        messages.error(request, "Can't complete this appointment. Check status.")
    
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
    
    return render(request, 'reservations/appointment_status.html', context)

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
