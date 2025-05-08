import time
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PatientsFile
from doctors.models import DrComment as dr_comment
from medimag.models import Comment as mag_comment
from docpages.models import Comment as post_comment
from clinics.models import ClinicComment as clinic_comment

# Create your views here.
@login_required()
def comments_view(request):
    return render(request, 'patients/comment_list.html')


@login_required
def comment_delete(request, model_type, id):
    MODEL_MAP = {
        'dr': dr_comment,
        'mag': mag_comment,
        'post': post_comment,
        'clinic': clinic_comment,
    }

    if model_type not in MODEL_MAP:
        raise Http404("نوع کامنت نامعتبر است")

    model = MODEL_MAP[model_type]
    comment = get_object_or_404(model, id=id, user=request.user)  # بررسی مالکیت
    comment.delete()

    messages.success(request, 'کامنت با موفقیت حذف شد')
    return redirect('patients:comments')


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from datetime import datetime
from .models import PatientsFile


@login_required
def patient_profile(request):
    """View and edit patient profile (updates both User and PatientsFile)"""
    user = request.user
    patient, created = PatientsFile.objects.get_or_create(
        user=user,
        defaults={
            'name': user.get_full_name() or user.first_name,
            'phone': user.phone,
            'email': user.email
        }
    )

    if request.method == 'POST':
        try:
            # 1. Update User model fields
            user.first_name = request.POST.get('f_name', user.first_name)
            user.last_name = request.POST.get('l_name', user.last_name)
            user.email = request.POST.get('email', user.email)

            # Only update phone if it's changed and not empty
            new_phone = request.POST.get('phone')
            if new_phone and new_phone != user.phone:
                user.phone = new_phone

            user.save()

            # 2. Update PatientFile model
            patient.name = f"{user.first_name} {user.last_name}".strip()
            patient.phone = user.phone
            patient.email = user.email
            patient.national_id = request.POST.get('national_id', patient.national_id)
            patient.medical_history = request.POST.get('medical_history', patient.medical_history)
            patient.gender = request.POST.get('gender', patient.gender)

            if 'city' in request.POST:
                patient.city_id = int(request.POST.get('city'))

            if 'birthdate' in request.POST and request.POST['birthdate']:
                patient.birthdate = datetime.strptime(
                    request.POST['birthdate'],
                    '%Y-%m-%d'
                ).date()

            patient.save()

            messages.success(request, "پروفایل با موفقیت به‌روزرسانی شد")
            return redirect('patients:patient_profile')

        except Exception as e:
            messages.error(request, f"خطا در به‌روزرسانی پروفایل: {str(e)}")

    # Prepare context for GET request
    context = {
        'patient': patient,
        'user': user,
        'birthdate': patient.birthdate.strftime('%Y-%m-%d') if patient.birthdate else ''
    }

    return render(request, 'patients/information.html', context)

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
    future_appointments = patient.get_upcoming_appointments()
    past_appointments = patient.get_past_appointments()
    appointments = patient.get_reservations().order_by('-day__date', '-time')

    context = {
        'patient': patient,
        'appointments': appointments,
        'past_appointments': past_appointments,
        'future_appointments': future_appointments,
        'status': status,
    }
    return render(request, 'patients/appointment.html', context)

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
