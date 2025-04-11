from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from .models import Doctor
from turn.models import Reservation


def doctor_list(request):
    """View to display list of doctors with search and filter functionality"""
    doctors = Doctor.objects.filter(is_available=True)
    
    # Filter by specialization if provided
    specialization = request.GET.get('specialization')
    if specialization:
        doctors = doctors.filter(specialization__icontains=specialization)
    
    # Filter by clinic if provided
    clinic_id = request.GET.get('clinic')
    if clinic_id:
        doctors = doctors.filter(clinic_id=clinic_id)
    
    context = {
        'doctors': doctors,
        'specializations': Doctor.objects.values_list('specialization', flat=True).distinct(),
    }
    return render(request, 'doctors/doctor_list.html', context)


def doctor_detail(request, doctor_id):
    """View to display doctor details and available appointment slots"""
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    # Get the doctor's availability
    availabilities = doctor.availabilities.all()
    
    # Get the doctor's existing appointments
    appointments = Reservation.objects.filter(doctor=doctor)
    
    context = {
        'doctor': doctor,
        'availabilities': availabilities,
        'appointments': appointments,
    }
    return render(request, 'doctors/doctor_detail.html', context)


@login_required
def doctor_dashboard(request):
    """View for doctor's dashboard with appointments and earnings"""
    # Check if user is a doctor
    try:
        doctor = request.user.doctor_profile
    except:
        return redirect('home')  # Redirect if user is not a doctor
    
    # Get time filters
    filter_period = request.GET.get('period', 'today')
    today = timezone.now().date()
    
    if filter_period == 'today':
        appointments = Reservation.objects.filter(doctor=doctor, day__date=today)
        period_start = today
    elif filter_period == 'week':
        week_start = today - timedelta(days=today.weekday())
        appointments = Reservation.objects.filter(doctor=doctor, day__date__gte=week_start, day__date__lte=today)
        period_start = week_start
    elif filter_period == 'month':
        month_start = today.replace(day=1)
        appointments = Reservation.objects.filter(doctor=doctor, day__date__gte=month_start, day__date__lte=today)
        period_start = month_start
    else:
        appointments = Reservation.objects.filter(doctor=doctor)
        period_start = None
    
    # Stats
    total_appointments = appointments.count()
    completed_appointments = appointments.filter(status=Reservation.STATUS_COMPLETED).count()
    earnings = appointments.filter(payment_status=Reservation.PAYMENT_PAID).aggregate(total=Sum('amount'))['total'] or 0
    
    # Upcoming appointments
    upcoming_appointments = Reservation.objects.filter(
        doctor=doctor,
        status=Reservation.STATUS_CONFIRMED,
        day__date__gte=today
    ).order_by('day__date', 'time')
    
    context = {
        'doctor': doctor,
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'earnings': earnings,
        'upcoming_appointments': upcoming_appointments,
        'period': filter_period,
    }
    return render(request, 'doctors/dashboard.html', context)


@login_required
def doctor_analytics(request):
    """View for doctor's analytics dashboard with detailed statistics"""
    # Check if user is a doctor
    try:
        doctor = request.user.doctor_profile
    except:
        return redirect('home')  # Redirect if user is not a doctor
    
    # Get time filters
    filter_period = request.GET.get('period', 'month')
    today = timezone.now().date()
    
    # Calculate date ranges based on filter
    if filter_period == 'month':
        # Last 30 days
        period_start = today - timedelta(days=30)
    elif filter_period == 'quarter':
        # Last 90 days
        period_start = today - timedelta(days=90)
    elif filter_period == 'year':
        # Last 365 days
        period_start = today - timedelta(days=365)
    else:
        # Default to month
        period_start = today - timedelta(days=30)
    
    # Get all appointments in the selected period
    appointments = Reservation.objects.filter(
        doctor=doctor,
        day__date__gte=period_start,
        day__date__lte=today
    )
    
    # Calculate overall stats
    total_appointments = appointments.count()
    completed_appointments = appointments.filter(status=Reservation.STATUS_COMPLETED).count()
    cancelled_appointments = appointments.filter(status=Reservation.STATUS_CANCELLED).count()
    completion_rate = (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0
    
    # Calculate earnings
    total_earnings = appointments.filter(payment_status=Reservation.PAYMENT_PAID).aggregate(total=Sum('amount'))['total'] or 0
    avg_earnings_per_appointment = total_earnings / completed_appointments if completed_appointments > 0 else 0
    
    # Appointment distribution by weekday
    weekday_distribution = appointments.values('day__weekday').annotate(count=Count('id')).order_by('day__weekday')
    
    # Patient demographics data (new vs returning patients)
    patient_ids = appointments.values_list('patient_id', flat=True)
    unique_patients = len(set(patient_ids))
    returning_patient_count = total_appointments - unique_patients
    new_patient_ratio = unique_patients / total_appointments if total_appointments > 0 else 0
    
    context = {
        'doctor': doctor,
        'period': filter_period,
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'cancelled_appointments': cancelled_appointments,
        'completion_rate': round(completion_rate, 1),
        'total_earnings': total_earnings,
        'avg_earnings_per_appointment': round(avg_earnings_per_appointment, 0),
        'weekday_distribution': weekday_distribution,
        'unique_patients': unique_patients,
        'returning_patient_count': returning_patient_count,
        'new_patient_ratio': round(new_patient_ratio * 100, 1),
    }
    
    return render(request, 'doctors/analytics.html', context)


@login_required
def update_appointment_status(request, appointment_id):
    """AJAX view to update appointment status"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    try:
        doctor = request.user.doctor_profile
        appointment = Reservation.objects.get(id=appointment_id, doctor=doctor)
    except:
        return JsonResponse({'error': 'Appointment not found or not authorized'}, status=404)
    
    new_status = request.POST.get('status')
    if new_status not in [Reservation.STATUS_CONFIRMED, Reservation.STATUS_COMPLETED, Reservation.STATUS_CANCELLED]:
        return JsonResponse({'error': 'Invalid status'}, status=400)
    
    appointment.status = new_status
    appointment.save()
    
    return JsonResponse({'success': True, 'status': new_status})
