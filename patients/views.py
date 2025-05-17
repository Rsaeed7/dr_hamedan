
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from weasyprint import HTML
from doctors.models import DrComment as dr_comment
from medimag.models import Comment as mag_comment
from docpages.models import Comment as post_comment
from clinics.models import ClinicComment as clinic_comment
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from datetime import datetime
from .models import PatientsFile
from django.views.generic import DetailView, CreateView, ListView
from django.urls import reverse, reverse_lazy
from .models import MedicalRecord, VisitEntry,MedicalReport,DrReportSettings
from .forms import VisitEntryForm, MedicalRecordForm, ReportForm,DrReportSettingsForm,EditReportForm
from django.views.generic.edit import CreateView

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




class MedicalRecordDetailView(DetailView):
    model = MedicalRecord
    template_name = 'patients/medical_record_detail.html'
    context_object_name = 'record'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['visit_form'] = VisitEntryForm()
        context['visits'] = self.object.visits.all()
        return context

class CreateMedicalRecordView(CreateView):
    model = MedicalRecord
    form_class = MedicalRecordForm
    template_name = 'patients/record_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.patient_id = kwargs.get('patient_id')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.doctor = self.request.user.doctor
        form.instance.patient_id = self.patient_id
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('patients:record-detail', args=[self.object.id])

class VisitEntryCreateView(CreateView):
    model = VisitEntry
    form_class = VisitEntryForm

    def form_valid(self, form):
        record = get_object_or_404(MedicalRecord, pk=self.kwargs['record_id'])
        form.instance.record = record
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('patients:record-detail', kwargs={'pk': self.kwargs['record_id']})

class CreateReportView(CreateView):
    model = MedicalReport
    form_class = ReportForm
    template_name = 'patients/create_report.html'
    success_url = reverse_lazy('patients:report_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = PatientsFile.objects.get(id=self.kwargs['patient_id'])
        context['patient'] = patient  # ارسال نام بیمار به تمپلیت
        return context
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        patient = PatientsFile.objects.get(id=self.kwargs['patient_id'])
        kwargs['patient_name'] = patient.name  # ارسال نام بیمار
        kwargs['patient_age'] = patient.age  # ارسال سن بیمار
        return kwargs

    def form_valid(self, form):
        form.instance.doctor = self.request.user.doctor
        form.instance.patient_id = self.kwargs['patient_id']
        form.instance.name = form.instance.patient.name  # تنظیم نام بیمار از مدل مرتبط

        return super().form_valid(form)


class ReportDetailView(DetailView):
    model = MedicalReport
    template_name = 'patients/report_detail.html'
    context_object_name = 'report'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.request.user.doctor
        template_settings = getattr(doctor, 'template_settings', None)
        context['background_image'] = template_settings.background_image.url if template_settings and template_settings.background_image else None
        context['custom_css'] = template_settings.custom_css if template_settings else ''
        context['saeed'] = 'saeed'
        return context

    def get(self, request, *args, **kwargs):
        if 'pdf' in request.GET:
            report = self.get_object()

            # دریافت تنظیمات قالب پزشک
            doctor = request.user.doctor
            template_settings = getattr(doctor, 'template_settings', None)
            background_image = template_settings.background_image.url if template_settings and template_settings.background_image else None
            custom_css = template_settings.custom_css if template_settings else ''

            # ارسال مقدار `background_image` و `custom_css` به قالب PDF
            html_string = render_to_string(
                'patients/report_pdf.html',
                {
                    'report': report,
                    'request': request,
                    'background_image': background_image,
                    'custom_css': custom_css,
                }
            )
            html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
            pdf = html.write_pdf()
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'filename=report_{report.id}.pdf'
            return response

        return super().get(request, *args, **kwargs)


class ReportListView(ListView):
    model = MedicalReport
    template_name = 'patients/report_list.html'
    context_object_name = 'reports'
    paginate_by = 10

    def get_queryset(self):
        query_name = self.request.GET.get('name', '')
        query_title = self.request.GET.get('title', '')
        query_dr_requesting = self.request.GET.get('dr_requesting', '')


        queryset = MedicalReport.objects.filter(doctor=self.request.user.doctor)

        if query_name:
            queryset = queryset.filter(name__icontains=query_name)
        if query_title:
            queryset = queryset.filter(title__icontains=query_title)
        if query_dr_requesting:
            queryset = queryset.filter(dr_requesting__icontains=query_dr_requesting)

        return queryset.order_by('-created_at')


@login_required
def edit_report(request, report_pk):
    report = get_object_or_404(MedicalReport, pk=report_pk)

    # فقط پزشک معالج بتواند ویرایش کند
    if request.user.doctor != report.doctor:
        return redirect('patients:report_list')

    if request.method == "POST":
        form = EditReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            return redirect('patients:report_detail', report_pk)  # استفاده از `report_pk`
    else:
        form = EditReportForm(instance=report)

    return render(request, 'patients/edit_report.html', {'form': form, 'report': report})




@login_required
def edit_report_settings(request):
    doctor = request.user.doctor
    settings, created = DrReportSettings.objects.get_or_create(doctor=doctor)

    if request.method == 'POST':
        form = DrReportSettingsForm(request.POST, request.FILES, instance=settings)
        if form.is_valid():
            form.save()
            return redirect('patients:report_settings')

    else:
        form = DrReportSettingsForm(instance=settings)

    return render(request, 'patients/report_settings.html', {'form': form})