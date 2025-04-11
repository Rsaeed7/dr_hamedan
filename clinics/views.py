from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.utils import timezone

from .models import Clinic
from doctors.models import Doctor
from turn.models import Reservation


def clinic_list(request):
    """View to display list of clinics with search functionality"""
    clinics = Clinic.objects.all()
    
    # Search by name or address
    search_query = request.GET.get('q')
    if search_query:
        clinics = clinics.filter(name__icontains=search_query) | clinics.filter(address__icontains=search_query)
    
    context = {
        'clinics': clinics,
    }
    return render(request, 'clinics/clinic_list.html', context)


def clinic_detail(request, clinic_id):
    """View to display clinic details and doctors"""
    clinic = get_object_or_404(Clinic, id=clinic_id)
    
    # Get all doctors in this clinic
    doctors = clinic.doctors.filter(is_available=True)
    
    # Get specialties
    specialties = clinic.specialties.all()
    
    # Get gallery images
    gallery = clinic.gallery.all()
    
    context = {
        'clinic': clinic,
        'doctors': doctors,
        'specialties': specialties,
        'gallery': gallery,
    }
    return render(request, 'clinics/clinic_detail.html', context)


@login_required
def clinic_dashboard(request):
    """View for clinic admin dashboard with stats and doctor management"""
    # Check if user is a clinic admin
    clinics = request.user.administered_clinics.all()
    if not clinics.exists():
        return redirect('home')  # Redirect if user is not a clinic admin
    
    # If user manages multiple clinics, let them choose
    clinic_id = request.GET.get('clinic')
    if clinic_id:
        clinic = get_object_or_404(Clinic, id=clinic_id, admin=request.user)
    else:
        clinic = clinics.first()
    
    # Get doctors in this clinic
    doctors = clinic.doctors.all()
    
    # Get appointments stats
    today = timezone.now().date()
    total_appointments = Reservation.objects.filter(doctor__in=doctors).count()
    today_appointments = Reservation.objects.filter(doctor__in=doctors, day__date=today).count()
    upcoming_appointments = Reservation.objects.filter(
        doctor__in=doctors,
        status=Reservation.STATUS_CONFIRMED,
        day__date__gte=today
    ).count()
    
    # Get financial stats
    total_earnings = Reservation.objects.filter(
        doctor__in=doctors,
        payment_status=Reservation.PAYMENT_PAID
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Get per-doctor stats
    doctor_stats = []
    for doctor in doctors:
        doctor_appointments = Reservation.objects.filter(doctor=doctor)
        doctor_earnings = doctor_appointments.filter(
            payment_status=Reservation.PAYMENT_PAID
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        doctor_stats.append({
            'doctor': doctor,
            'appointments': doctor_appointments.count(),
            'earnings': doctor_earnings,
        })
    
    context = {
        'clinics': clinics,
        'selected_clinic': clinic,
        'doctors': doctors,
        'total_appointments': total_appointments,
        'today_appointments': today_appointments,
        'upcoming_appointments': upcoming_appointments,
        'total_earnings': total_earnings,
        'doctor_stats': doctor_stats,
    }
    return render(request, 'clinics/dashboard.html', context)
