from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PatientsFile

# Create your views here.

@login_required
def patient_profile(request):
    """View and edit patient profile"""
    # Get or create the patient file for this user
    patient, created = PatientsFile.objects.get_or_create(
        user=request.user,
        defaults={
            'name': request.user.get_full_name() or request.user.username,
            'phone': ''
        }
    )
    
    if request.method == 'POST':
        # Update patient information
        patient.name = request.POST.get('name', patient.name)
        patient.phone = request.POST.get('phone', patient.phone)
        patient.national_id = request.POST.get('national_id', patient.national_id)
        patient.medical_history = request.POST.get('medical_history', patient.medical_history)
        patient.notes = request.POST.get('notes', patient.notes)
        
        if 'birthdate' in request.POST and request.POST['birthdate']:
            from datetime import datetime
            patient.birthdate = datetime.strptime(request.POST['birthdate'], '%Y-%m-%d').date()
        
        patient.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('patients:patient_profile')
    
    context = {
        'patient': patient,
    }
    
    return render(request, 'patients/profile.html', context)

@login_required
def patient_appointments(request):
    """View patient's appointments"""
    # Get the patient file for this user
    try:
        patient = PatientsFile.objects.get(user=request.user)
    except PatientsFile.DoesNotExist:
        messages.error(request, "Please complete your profile first.")
        return redirect('patients:patient_profile')
    
    # Get filter parameters
    status = request.GET.get('status', 'all')
    
    # Get appointments
    if status == 'upcoming':
        appointments = patient.get_upcoming_appointments()
    elif status == 'past':
        appointments = patient.get_past_appointments()
    else:
        appointments = patient.get_reservations().order_by('-day__date', '-time')
    
    context = {
        'patient': patient,
        'appointments': appointments,
        'status': status,
    }
    
    return render(request, 'patients/appointments.html', context)

@login_required
def patient_dashboard(request):
    """Patient's dashboard with upcoming appointments and quick links"""
    # Get the patient file for this user
    try:
        patient = PatientsFile.objects.get(user=request.user)
    except PatientsFile.DoesNotExist:
        messages.error(request, "Please complete your profile first.")
        return redirect('patients:patient_profile')
    
    # Get upcoming appointments
    upcoming_appointments = patient.get_upcoming_appointments()[:3]
    
    context = {
        'patient': patient,
        'upcoming_appointments': upcoming_appointments,
    }
    
    return render(request, 'patients/dashboard.html', context)
