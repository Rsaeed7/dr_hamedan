from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Clinic, ClinicSpecialty, ClinicGallery,ClinicComment
from doctors.models import Doctor
from reservations.models import Reservation
from django.db.models import Q
from django.views.generic import ListView


class ClinicListView(ListView):
    model = Clinic
    template_name = 'clinics/clinic_list.html'
    context_object_name = 'clinics'
    paginate_by = 10  # تعداد آیتم‌ها در هر صفحه

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('query', '')
        specialty = self.request.GET.get('specialty', '')

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(address__icontains=query)
            )

        if specialty:
            queryset = queryset.filter(specialties__name__icontains=specialty).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # اضافه کردن پارامترهای جستجو به context برای نمایش در تمپلیت
        context['query'] = self.request.GET.get('query', '')
        context['specialty'] = self.request.GET.get('specialty', '')
        return context


@login_required
def clinic_detail(request, pk):
    clinic = get_object_or_404(Clinic, pk=pk)
    doctors = Doctor.objects.filter(clinic=clinic, is_available=True)
    comments = ClinicComment.objects.filter(clinic=clinic, status='confirmed')
    clinic.increment_view_count()

    if request.method == 'POST':
        recommendation = request.POST.get('recommendation')
        rating = request.POST.get('rating')
        text = request.POST.get('text')

        # اعتبارسنجی ساده
        if not text or not rating:
            messages.error(request, 'لطفاً امتیاز و متن نظر را وارد کنید')
        else:
            ClinicComment.objects.create(
                clinic=clinic,
                user=request.user,
                recommendation=recommendation,
                rate=rating,
                text=text,
            )
            messages.success(request, 'نظر شما با موفقیت ثبت شد')
            return redirect('clinics:clinic_detail', pk=clinic.pk)

    context = {
        'clinic': clinic,
        'doctors': doctors,
        'gallery': clinic.gallery.all(),
        'specialties': clinic.specialties.all(),
        'comments': comments,
        'stars_range': range(5),
    }

    return render(request, 'clinics/clinic_detail.html', context)

@login_required
def clinic_dashboard(request):
    """Clinic admin dashboard"""
    # Check if user is a clinic admin
    try:
        clinic = Clinic.objects.get(admin=request.user)
    except Clinic.DoesNotExist:
        return redirect('doctors:doctor_list')  # Redirect if user is not a clinic admin
    
    # Get all doctors in this clinic
    doctors = Doctor.objects.filter(clinic=clinic)
    
    # Get upcoming appointments for all doctors
    upcoming_appointments = Reservation.objects.filter(
        doctor__in=doctors,
        status__in=['pending', 'confirmed']
    ).order_by('day__date', 'time')[:10]
    
    context = {
        'clinic': clinic,
        'doctors': doctors,
        'upcoming_appointments': upcoming_appointments,
    }
    
    return render(request, 'clinics/dashboard.html', context)

@login_required
def clinic_profile(request):
    """Manage clinic profile"""
    # Check if user is a clinic admin
    try:
        clinic = Clinic.objects.get(admin=request.user)
    except Clinic.DoesNotExist:
        return redirect('doctors:doctor_list')  # Redirect if user is not a clinic admin
    
    if request.method == 'POST':
        # Process form submission to update clinic profile
        clinic.name = request.POST.get('name', clinic.name)
        clinic.address = request.POST.get('address', clinic.address)
        clinic.phone = request.POST.get('phone', clinic.phone)
        clinic.email = request.POST.get('email', clinic.email)
        clinic.description = request.POST.get('description', clinic.description)
        
        if 'logo' in request.FILES:
            clinic.logo = request.FILES['logo']
        
        clinic.save()
        
        # Handle specialty updates
        if 'specialty_name' in request.POST and 'specialty_description' in request.POST:
            ClinicSpecialty.objects.create(
                clinic=clinic,
                name=request.POST['specialty_name'],
                description=request.POST['specialty_description']
            )
        
        # Handle gallery uploads
        if 'gallery_image' in request.FILES:
            ClinicGallery.objects.create(
                clinic=clinic,
                image=request.FILES['gallery_image'],
                title=request.POST.get('image_title', '')
            )
        
        return redirect('clinics:clinic_profile')
    
    context = {
        'clinic': clinic,
        'specialties': clinic.specialties.all(),
        'gallery': clinic.gallery.all(),
    }
    
    return render(request, 'clinics/profile.html', context)

@login_required
def clinic_doctors(request):
    """Manage doctors affiliated with the clinic"""
    # Check if user is a clinic admin
    try:
        clinic = Clinic.objects.get(admin=request.user)
    except Clinic.DoesNotExist:
        return redirect('doctors:doctor_list')  # Redirect if user is not a clinic admin
    
    if request.method == 'POST':
        # Process doctor association/disassociation
        doctor_id = request.POST.get('doctor_id')
        action = request.POST.get('action')
        
        if doctor_id and action:
            doctor = get_object_or_404(Doctor, id=doctor_id)
            
            if action == 'add' and (doctor.is_independent or doctor.clinic is None):
                doctor.clinic = clinic
                doctor.is_independent = False
                doctor.save()
            
            elif action == 'remove' and doctor.clinic == clinic:
                doctor.clinic = None
                doctor.is_independent = True
                doctor.save()
    
    # Get all doctors in this clinic
    clinic_doctors = Doctor.objects.filter(clinic=clinic)
    
    # Get independent doctors (for potential addition)
    independent_doctors = Doctor.objects.filter(Q(is_independent=True) | Q(clinic=None))
    
    context = {
        'clinic': clinic,
        'clinic_doctors': clinic_doctors,
        'independent_doctors': independent_doctors,
    }
    
    return render(request, 'clinics/doctors.html', context)

@login_required
def clinic_appointments(request):
    """Manage all appointments for the clinic's doctors"""
    # Check if user is a clinic admin
    try:
        clinic = Clinic.objects.get(admin=request.user)
    except Clinic.DoesNotExist:
        return redirect('doctors:doctor_list')  # Redirect if user is not a clinic admin
    
    # Get all doctors in this clinic
    doctors = Doctor.objects.filter(clinic=clinic)
    
    # Get filter parameters
    doctor_id = request.GET.get('doctor_id', 'all')
    status = request.GET.get('status', 'all')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base query - all appointments for clinic doctors
    appointments = Reservation.objects.filter(doctor__in=doctors)
    
    # Apply filters
    if doctor_id != 'all':
        appointments = appointments.filter(doctor_id=doctor_id)
    
    if status != 'all':
        appointments = appointments.filter(status=status)
    
    if date_from:
        try:
            from datetime import datetime
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            appointments = appointments.filter(day__date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            from datetime import datetime
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            appointments = appointments.filter(day__date__lte=date_to)
        except ValueError:
            pass
    
    # Order by date and time
    appointments = appointments.order_by('day__date', 'time')
    
    context = {
        'clinic': clinic,
        'doctors': doctors,
        'appointments': appointments,
        'selected_doctor': doctor_id,
        'status': status,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'clinics/appointments.html', context)

@login_required
def delete_gallery_image(request, pk):
    """Delete a gallery image"""
    image = get_object_or_404(ClinicGallery, pk=pk)
    
    # Only clinic admin can delete images
    try:
        clinic = Clinic.objects.get(admin=request.user)
        if image.clinic != clinic:
            return redirect('clinics:clinic_profile')
    except Clinic.DoesNotExist:
        return redirect('doctors:doctor_list')
    
    if request.method == 'POST':
        image.delete()
    
    return redirect('clinics:clinic_profile')
