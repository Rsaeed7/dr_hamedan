import jdatetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from patients.models import MedicalRecord
from .models import Doctor, DoctorAvailability, Specialization, Clinic, City, DrComment, CommentTips ,Email,Supplementary_insurance, DoctorRegistration,EmailTemplate
from reservations.models import Reservation, ReservationDay
from datetime import datetime, timedelta
from django.db.models import  Sum, Avg
from django.utils import timezone
from wallet.models import Transaction
from utils.utils import send_notification
from medimag.models import MagArticle
from docpages.models import Post
from django.db.models import Q
from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from .forms import EmailForm, DoctorRegistrationForm ,EmailTemplateForm
from homecare.models import Service
from reservations.turn_maker import create_availability_days_for_day_of_week
from reservations.services import BookingService, AppointmentService
import random


def index(request):
    doctors_list = list(Doctor.objects.filter(is_available=True))
    random.shuffle(doctors_list)
    doctors = doctors_list[:10]

    online_visit_doctors = Doctor.objects.filter(is_available=True, online_visit=True).order_by('-availability__is_available')
    clinics = Clinic.objects.all()
    specializations = Specialization.objects.all().order_by('name')
    articles = MagArticle.objects.all()
    context = {
        'doctors': doctors,
        'clinics': clinics,
        'specializations': specializations,
        'articles': articles,
        'online_visit_doctors': online_visit_doctors,
        'posts' : Post.objects.filter(status='published')[:13]
    }
    return render(request, 'index/homepage.html', context)


def specializations(request):
    services = Service.objects.all()
    return render(request, 'doctors/specialization_list.html' , {'services': services})


def explore(request):
    """
    Enhanced explore view with lazy loading, search, and filtering
    """
    from django.core.paginator import Paginator
    from django.http import JsonResponse
    from django.template.loader import render_to_string
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    media_type = request.GET.get('media_type', 'all')  # all, image, video, none
    specialty = request.GET.get('specialty', '')
    page = request.GET.get('page', 1)
    
    # Base queryset - published posts with related data
    posts = Post.objects.filter(status='published').select_related(
        'doctor', 'doctor__user'
    ).prefetch_related('medical_lenses', 'post_likes')
    
    # Apply search filter
    if search_query:
        from django.db import models as db_models
        posts = posts.filter(
            db_models.Q(title__icontains=search_query) |
            db_models.Q(content__icontains=search_query) |
            db_models.Q(doctor__user__first_name__icontains=search_query) |
            db_models.Q(doctor__user__last_name__icontains=search_query) |
            db_models.Q(medical_lenses__name__icontains=search_query)
        ).distinct()
    
    # Apply media type filter
    if media_type != 'all':
        posts = posts.filter(media_type=media_type)
    
    # Apply specialty filter
    if specialty:
        posts = posts.filter(doctor__specialization__icontains=specialty)
    
    # Order by creation date (newest first)
    posts = posts.order_by('-created_at')
    
    # Paginate results (12 posts per page for grid layout)
    paginator = Paginator(posts, 12)
    posts_page = paginator.get_page(page)
    
    # Handle AJAX requests for lazy loading
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        posts_html = render_to_string(
            'index/explore_posts_partial.html', 
            {'posts': posts_page, 'request': request}
        )
        
        return JsonResponse({
            'success': True,
            'posts_html': posts_html,
            'has_next': posts_page.has_next(),
            'next_page': posts_page.next_page_number() if posts_page.has_next() else None,
            'total_count': paginator.count,
            'current_page': posts_page.number,
            'total_pages': paginator.num_pages
        })
    
    # Get specializations for filter dropdown
    from doctors.models import Doctor
    specializations = Doctor.objects.values_list('specialization', flat=True).distinct().order_by('specialization')
    
    # Get statistics
    stats = {
        'total_posts': Post.objects.filter(status='published').count(),
        'video_posts': Post.objects.filter(status='published', media_type='video').count(),
        'image_posts': Post.objects.filter(status='published', media_type='image').count(),
        'doctors_count': Doctor.objects.count()
    }
    
    context = {
        'posts': posts_page,
        'search_query': search_query,
        'media_type': media_type,
        'specialty': specialty,
        'specializations': specializations,
        'stats': stats,
    }
    return render(request, 'index/medexplore.html', context)


def doctor_registration(request):
    """Doctor registration view for new doctors to apply"""
    if request.method == 'POST':
        form = DoctorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            registration = form.save()
            messages.success(request, 'درخواست عضویت شما با موفقیت ثبت شد. پس از بررسی، نتیجه از طریق ایمیل اطلاع‌رسانی خواهد شد.')
            return redirect('doctors:doctor_registration')
    else:
        form = DoctorRegistrationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'doctors/doctor_registration.html', context)


class DoctorListView(ListView):
    template_name = 'doctors/expertise_list.html'
    model = Doctor
    context_object_name = 'doctors'
    paginate_by = 10



    def get_queryset(self):
        queryset = super().get_queryset().filter(is_available=True)
        params = self.get_filter_params()

        # اعمال فیلترها
        if params['query']:
            queryset = queryset.filter(
                Q(user__first_name__icontains=params['query']) |
                Q(user__last_name__icontains=params['query']) |
                Q(specialization__name__icontains=params['query'])
            )

            # فیلتر تخصص - فقط اگر مقدار انتخاب شده باشد
        if params['specialty'] and params['specialty'][0]:
            queryset = queryset.filter(specialization__name__in=params['specialty'])

            # فیلتر جنسیت
        if params['gender']:
            queryset = queryset.filter(gender=params['gender'])

            # فیلتر شهر - فقط اگر مقدار انتخاب شده باشد
        if params['city'] and params['city'][0]:
            queryset = queryset.filter(city__name__in=params['city'])

        if params['supplementary'] and params['supplementary'][0]:
                queryset = queryset.filter(Insurance__name__in=params['supplementary'])

            # فیلتر کلینیک
        if params['clinic']:
            queryset = queryset.filter(clinic__name__icontains=params['clinic'])

            # فیلتر روزهای کاری - فقط اگر مقدار انتخاب شده باشد
        if params['days'] and params['days'][0]:
            day_mapping = {
                'شنبه': 0, 'یکشنبه': 1, 'دوشنبه': 2,
                'سه‌شنبه': 3, 'چهارشنبه': 4, 'پنج‌شنبه': 5
            }
            day_numbers = [day_mapping[day] for day in params['days'] if day in day_mapping]
            if day_numbers:
                queryset = queryset.filter(
                    availabilities__day_of_week__in=day_numbers
                ).distinct()

        # محاسبه میانگین امتیازها
        queryset = queryset.annotate(
            avg_comment_rating=Avg(
                'comments__rate',
                filter=Q(comments__status='confirmed')
            )
        )

        # مرتب‌سازی
        if params['sort'] == 'پر بازدیدترین':
            queryset = queryset.order_by('-view_count')
        elif params['sort'] == 'بالاترین امتیاز':
            queryset = queryset.order_by('-avg_comment_rating')
        elif params['sort'] == 'نزدیک‌ترین نوبت خالی':
            queryset = sorted(queryset, key=lambda doctor: doctor.get_first_available_day() or jdatetime.date(1450, 10, 10))

        return queryset

    def get_filter_params(self):
        return {
            'query': self.request.GET.get('query', ''),
            'specialty': self.request.GET.getlist('specialty'),
            'gender': self.request.GET.get('gender', ''),
            'sort': self.request.GET.get('sort', ''),
            'days': self.request.GET.getlist('days'),
            'city': self.request.GET.getlist('city'),
            'clinic': self.request.GET.get('clinic', ''),
            'supplementary': self.request.GET.getlist('supplementary')
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.get_filter_params()

        context.update({
            'clinics': Clinic.objects.all(),
            'specializations': Specialization.objects.all().order_by('name'),
            'Insurance': Supplementary_insurance.objects.all().order_by('name'),
            'supplementary_list': params['supplementary'],
            'current_filters': params,
            'day_list': ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه'],
            'specialty': params['specialty'],
            'days': params['days'],
            'city_list': params['city'],
            'available_doctors':  Doctor.objects.filter(availability__is_available=True ).select_related('user'),

        })
        return context


def doctor_detail(request, pk):
    """
    The medical page detail should not be with the doctor's ID, it should be based on the name in English or ...
    """
    """نمایش اطلاعات کامل یک پزشک"""
    doctor = get_object_or_404(Doctor, pk=pk)

    # دریافت آمار و اطلاعات پزشک
    comments = DrComment.objects.filter(doctor=doctor, status='confirmed')
    tips = CommentTips.objects.all()
    doctor.increment_view_count()
    posts = doctor.posts.filter(status='published')[:6]

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('account:register')
        recommendation = request.POST.get('recommendation')
        rating = request.POST.get('rating')
        text = request.POST.get('text')
        tips_ids = request.POST.getlist('tips')
        time = request.POST.get('time')

        if not text or not rating:
            messages.error(request, 'لطفاً امتیاز و متن نظر را وارد کنید')
        else:
            comment = DrComment.objects.create(
                doctor=doctor,
                user=request.user,
                recommendation=recommendation,
                rate=int(rating),
                text=text,
                waiting_time=time,
            )

            # اتصال مستقیم بر اساس IDها
            comment.tips.set(tips_ids)

            messages.success(request, 'نظر شما با موفقیت ثبت شد')
            return redirect('doctors:doctor_detail', pk=doctor.pk)

    # استفاده از سرویس برای دریافت روزهای آزاد
    available_days = BookingService.get_available_days_for_doctor(doctor.id, days_ahead=7)

    context = {
        'doctor': doctor,
        'available_days': available_days,
        'comments': comments,
        'stars_range':  range(5, 0, -1) ,
        'tips': tips,
        'posts':posts
    }

    return render(request, 'doctors/dr_detail.html', context)


@login_required
def doctor_dashboard(request):
    """داشبورد شخصی پزشک"""
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')

    # دریافت آمار برای داشبورد
    total_appointments = Reservation.objects.filter(doctor=doctor).count()
    upcoming_appointments = Reservation.objects.filter(
        doctor=doctor,
        day__date__gte=timezone.now().date()
    ).count()

    # دریافت نوبت‌های امروز
    today = timezone.now().date()
    todays_appointments = Reservation.objects.filter(
        doctor=doctor,
        day__date=today
    ).order_by('time')

    # محاسبه کل درآمد
    total_earnings = Transaction.objects.filter(
        user=doctor.user,
        transaction_type__in=['payment', 'deposit'],
        status='completed'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'doctor': doctor,
        'total_appointments': total_appointments,
        'upcoming_appointments': upcoming_appointments,
        'todays_appointments': todays_appointments,
        'total_earnings': total_earnings
    }

    return render(request, 'doctors/doctor_dashboard.html', context)


@login_required
def doctor_availability(request):
    """مدیریت زمان‌بندی هفتگی پزشک"""
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')

    if request.method == 'POST':
        # پردازش داده‌های فرم برای بروزرسانی زمان‌بندی
        day_of_week = request.POST.get('day_of_week')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        if day_of_week and start_time and end_time:
            DoctorAvailability.objects.create(
                doctor=doctor,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time
            )
            return redirect('doctors:doctor_availability')

    # دریافت تمام زمان‌بندی‌های این پزشک
    availabilities = DoctorAvailability.objects.filter(doctor=doctor).order_by('day_of_week', 'start_time')

    context = {
        'doctor': doctor,
        'available_days': availabilities,
    }

    return render(request, 'doctors/doctor_availability.html', context)


@login_required
def doctor_earnings(request):
    """نمایش درآمد پزشک در یک بازه زمانی"""
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')

    # دریافت تمام تراکنش‌های درآمد
    transactions = Transaction.objects.filter(
        user=doctor.user,
        transaction_type__in=['payment', 'deposit'],
        status='completed'
    ).order_by('-created_at')

    # محاسبه آمار
    total_earnings = transactions.aggregate(Sum('amount'))['amount__sum'] or 0

    # درآمد ماه جاری
    current_month = timezone.now().month
    current_year = timezone.now().year
    current_month_earnings = Transaction.objects.filter(
        user=doctor.user,
        transaction_type__in=['payment', 'deposit'],
        status='completed',
        created_at__month=current_month,
        created_at__year=current_year
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # درآمد ماه گذشته
    last_month = current_month - 1 if current_month > 1 else 12
    last_month_year = current_year if current_month > 1 else current_year - 1
    last_month_earnings = Transaction.objects.filter(
        user=doctor.user,
        transaction_type__in=['payment', 'deposit'],
        status='completed',
        created_at__month=last_month,
        created_at__year=last_month_year
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # محاسبه رشد ماهانه
    month_growth = 0
    if last_month_earnings > 0:
        month_growth = ((current_month_earnings - last_month_earnings) / last_month_earnings) * 100

    # دریافت تعداد کل نوبت‌های تکمیل شده
    total_completed_appointments = Reservation.objects.filter(
        doctor=doctor,
        status='completed'
    ).count()

    # محاسبه میانگین درآمد به ازای هر نوبت
    avg_earnings_per_appointment = 0
    if total_completed_appointments > 0:
        avg_earnings_per_appointment = total_earnings / total_completed_appointments

    # دریافت نوبت‌های تکمیل شده ماه گذشته
    completed_appointments_last_month = Reservation.objects.filter(
        doctor=doctor,
        status='completed',
        day__date__month=last_month,
        day__date__year=last_month_year
    ).count()

    # دریافت پرداخت‌های اخیر
    recent_payments = transactions[:5]

    context = {
        'doctor': doctor,
        'transactions': transactions,
        'total_earnings': total_earnings,
        'current_month_earnings': current_month_earnings,
        'last_month_earnings': last_month_earnings,
        'month_growth': month_growth,
        'total_completed_appointments': total_completed_appointments,
        'avg_earnings_per_appointment': avg_earnings_per_appointment,
        'completed_appointments_last_month': completed_appointments_last_month,
        'recent_payments': recent_payments
    }

    return render(request, 'doctors/doctor_earnings.html', context)


@login_required
def doctor_appointments(request):
    """نمایش و مدیریت نوبت‌های پزشک"""
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')

    # دریافت پارامترهای فیلتر
    status = request.GET.get('status', 'all')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # تبدیل تاریخ‌ها با مدیریت خطا بهتر
    date_from_obj = None
    date_to_obj = None
    
    if date_from:
        try:
            from datetime import datetime
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
        except ValueError:
            from django.contrib import messages
            messages.warning(request, 'فرمت تاریخ شروع نامعتبر است')

    if date_to:
        try:
            from datetime import datetime
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            from django.contrib import messages
            messages.warning(request, 'فرمت تاریخ پایان نامعتبر است')

    # استفاده از سرویس برای دریافت نوبت‌ها با بهینه‌سازی query
    appointments = BookingService.get_doctor_appointments(
        doctor=doctor,
        date_from=date_from_obj,
        date_to=date_to_obj,
        status_filter=status
    ).select_related(
        'patient', 'patient__user', 'day'
    ).prefetch_related(
        'patient__medicalrecord_set'
    )
    
    # اضافه کردن پرونده پزشکی به هر نوبت
    for appointment in appointments:
        if appointment.patient:
            record = appointment.patient.medicalrecord_set.filter(doctor=doctor).first()
            appointment.medical_record = record
        else:
            appointment.medical_record = None

    # افزودن pagination
    from django.core.paginator import Paginator
    paginator = Paginator(appointments, 20)  # نمایش 20 نوبت در هر صفحه
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # آمار برای نمایش
    total_appointments = appointments.count()
    has_filters = any([status != 'all', date_from, date_to])

    context = {
        'doctor': doctor,
        'appointments': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages,
        'paginator': paginator,
        'status': status,
        'date_from': date_from,
        'date_to': date_to,
        'total_appointments': total_appointments,
        'has_filters': has_filters,
    }

    return render(request, 'doctors/appointments.html', context)


@login_required
def doctor_profile(request):
    """نمایش و ویرایش اطلاعات پروفایل پزشک"""
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'personal_info':
            # بروزرسانی اطلاعات شخصی
            user = doctor.user
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.email = request.POST.get('email')
            user.save()

            doctor.phone = request.POST.get('phone', '')

            # مدیریت آپلود تصویر پروفایل
            if 'profile_image' in request.FILES:
                doctor.profile_image = request.FILES['profile_image']

            doctor.save()

            messages.success(request, 'اطلاعات شخصی با موفقیت بروزرسانی شد.')

        elif form_type == 'professional_info':
            # بروزرسانی اطلاعات حرفه‌ای
            doctor.specialization = request.POST.get('specialization')
            doctor.license_number = request.POST.get('license_number', '')
            doctor.bio = request.POST.get('bio', '')
            doctor.save()

            messages.success(request, 'اطلاعات حرفه‌ای با موفقیت بروزرسانی شد.')

        elif form_type == 'change_password':
            # تغییر رمز عبور
            user = doctor.user
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not user.check_password(current_password):
                messages.error(request, 'رمز عبور فعلی نادرست است.')
            elif new_password != confirm_password:
                messages.error(request, 'رمزهای عبور جدید مطابقت ندارند.')
            else:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'رمز عبور با موفقیت تغییر کرد. لطفا دوباره وارد شوید.')
                return redirect('login')

        return redirect('doctors:doctor_profile')

    context = {
        'doctor': doctor,
    }

    return render(request, 'doctors/doctor_profile.html', context)


@login_required
def confirm_appointment(request, pk):
    """تایید یک نوبت در انتظار"""
    try:
        doctor = request.user.doctor
        appointment = get_object_or_404(Reservation, pk=pk, doctor=doctor, status='pending')

        if request.method == 'POST':
            appointment.status = 'confirmed'
            appointment.save()

            # ارسال اعلان به بیمار
            if appointment.patient and appointment.patient.user:
                message = f"نوبت شما با دکتر {doctor.user.last_name} در تاریخ {appointment.day.date} ساعت {appointment.time} تایید شد."
                send_notification(appointment.patient.user, 'نوبت تایید شد', message)

            messages.success(request, 'نوبت با موفقیت تایید شد.')

        return redirect('doctors:doctor_appointments')

    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')


@login_required
def complete_appointment(request, pk):
    """علامت‌گذاری یک نوبت به عنوان تکمیل شده"""
    try:
        doctor = request.user.doctor
        appointment = get_object_or_404(Reservation, pk=pk, doctor=doctor, status='confirmed')

        if request.method == 'POST':
            appointment.status = 'completed'
            appointment.save()

            # ارسال اعلان به بیمار
            if appointment.patient and appointment.patient.user:
                message = f"نوبت شما با دکتر {doctor.user.last_name} در تاریخ {appointment.day.date} ساعت {appointment.time} به عنوان تکمیل شده علامت‌گذاری شد."
                send_notification(appointment.patient.user, 'نوبت تکمیل شد', message)

            messages.success(request, 'نوبت به عنوان تکمیل شده علامت‌گذاری شد.')

        return redirect('doctors:doctor_appointments')

    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')


@login_required
def cancel_appointment(request, pk):
    """لغو یک نوبت"""
    try:
        doctor = request.user.doctor
        appointment = get_object_or_404(Reservation, pk=pk, doctor=doctor)

        if request.method == 'POST':
            old_status = appointment.status
            appointment.status = 'cancelled'
            appointment.save()

            # مدیریت بازپرداخت در صورت پرداخت
            if appointment.payment_status == 'paid':
                appointment.cancel_appointment(refund=True)

            # ارسال اعلان به بیمار
            if appointment.patient and appointment.patient.user:
                message = f"نوبت شما با دکتر {doctor.user.last_name} در تاریخ {appointment.day.date} ساعت {appointment.time} لغو شد."
                send_notification(appointment.patient.user, 'نوبت لغو شد', message)

            messages.success(request, 'نوبت با موفقیت لغو شد.')

        return redirect('doctors:doctor_appointments')

    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')


@login_required
def toggle_availability(request):
    """تغییر وضعیت کلی دسترسی پزشک"""
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')

    if request.method == 'POST':
        doctor.is_available = not doctor.is_available
        doctor.save()

        status = "فعال" if doctor.is_available else "غیرفعال"
        messages.success(request, f"رزرو نوبت با موفقیت {status} شد.")

    return redirect('doctors:doctor_availability')


@login_required
def add_availability_day(request):
    """افزودن یک روز جدید به زمان‌بندی"""
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')

    if request.method == 'POST':
        day_of_week = request.POST.get('day_of_week')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        if day_of_week and start_time and end_time:
            try:
                day_of_week = int(day_of_week)
                
                # تبدیل رشته‌های زمان به اشیاء time
                start_time_obj = datetime.strptime(start_time, '%H:%M').time()
                end_time_obj = datetime.strptime(end_time, '%H:%M').time()
                
                # بررسی اینکه زمان پایان بعد از زمان شروع باشد
                if start_time_obj >= end_time_obj:
                    messages.error(request, "زمان پایان باید بعد از زمان شروع باشد.")
                    return redirect('doctors:add_availability_day')

                # ایجاد روز جدید در زمان‌بندی
                availability, created = DoctorAvailability.objects.get_or_create(
                    doctor=doctor,
                    day_of_week=day_of_week,
                    defaults={
                        'start_time': start_time_obj,
                        'end_time': end_time_obj
                    }
                )
                
                if not created:
                    # اگر روز از قبل وجود داشت، زمان‌ها را بروزرسانی کن
                    availability.start_time = start_time_obj
                    availability.end_time = end_time_obj
                    availability.save()
                    messages.info(request, "زمان‌بندی موجود بروزرسانی شد.")
                else:
                    messages.success(request, "زمان‌بندی جدید با موفقیت افزوده شد.")
                
                # استفاده از turn_maker برای ایجاد روزهای حضور در طول سال
                try:
                    result = create_availability_days_for_day_of_week(
                        doctor,
                        day_of_week,
                        start_time_obj,
                        end_time_obj
                    )
                    
                    success_message = f"""روزهای حضور جدید با موفقیت ایجاد شد:
                    - {result['days_created']} روز جدید افزوده شد
                    - {result['days_updated']} روز موجود بروزرسانی شد
                    - روزهای تعطیل رسمی به‌طور خودکار غیرفعال شدند
                    - بیماران می‌توانند در این روزها نوبت رزرو کنند"""
                    
                    messages.success(request, success_message)
                    
                except Exception as e:
                    messages.warning(request, f"زمان‌بندی ایجاد شد اما خطا در ایجاد روزهای حضور: {str(e)}")
                
                return redirect('doctors:doctor_availability')
                
            except ValueError:
                messages.error(request, "فرمت روز یا زمان نامعتبر است.")
        else:
            messages.error(request, "تمام فیلدها الزامی هستند.")

    context = {
        'doctor': doctor,
        'days_of_week': DoctorAvailability.DAYS_OF_WEEK,
    }

    return render(request, 'doctors/add_availability_day.html', context)


@login_required
def update_settings(request):
    """بروزرسانی تنظیمات زمان‌بندی پزشک"""
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        messages.error(request, "پزشک مورد نظر یافت نشد.")
        return redirect('doctors:doctor_list')

    if request.method != 'POST':
        return redirect('doctors:doctor_availability')

    # تعیین مسیر ریدایرکت پیش‌فرض
    redirect_url = 'doctors:doctor_availability'  # مسیر اول (پیش‌فرض)

    try:
        consultation_fee = request.POST.get('consultation_fee')
        consultation_duration = request.POST.get('consultation_duration')
        online_visit_fee = request.POST.get('online_visit_fee')
        online_visit = request.POST.get('online_visit') == 'on'

        if online_visit_fee:  # اگر شرط دوم برقرار بود
            redirect_url = 'chat:chat_room_list'  # مسیر دوم

        if consultation_fee and consultation_duration:
            doctor.consultation_fee = float(consultation_fee)
            doctor.consultation_duration = int(consultation_duration)

        if online_visit_fee:
            doctor.online_visit_fee = float(online_visit_fee)
            doctor.online_visit = online_visit

        doctor.save()
        messages.success(request, "تنظیمات با موفقیت بروزرسانی شد.")

    except ValueError:
        messages.error(request, "مقادیر وارد شده نامعتبر هستند.")
    except Exception as e:
        messages.error(request, f"خطا در بروزرسانی تنظیمات: {str(e)}")

    return redirect(redirect_url)


@login_required
def delete_availability_day(request, pk):
    """حذف یک روز از زمان‌بندی"""
    try:
        doctor = request.user.doctor
        availability = get_object_or_404(DoctorAvailability, pk=pk, doctor=doctor)
    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')

    if request.method == 'POST':
        availability.delete()
        messages.success(request, "روز مورد نظر با موفقیت حذف شد.")

    return redirect('doctors:doctor_availability')


@login_required
def edit_availability_day(request, pk):
    """ویرایش محدوده زمانی یک روز در زمان‌بندی"""
    try:
        doctor = request.user.doctor
        availability = get_object_or_404(DoctorAvailability, pk=pk, doctor=doctor)
    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')

    if request.method == 'POST':
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        if start_time and end_time:
            try:
                # تجزیه زمان‌ها
                start_time_obj = datetime.strptime(start_time, '%H:%M').time()
                end_time_obj = datetime.strptime(end_time, '%H:%M').time()

                # بروزرسانی زمان‌بندی
                availability.start_time = start_time_obj
                availability.end_time = end_time_obj
                availability.save()

                messages.success(request, "زمان‌بندی با موفقیت بروزرسانی شد.")
                return redirect('doctors:doctor_availability')
            except ValueError:
                messages.error(request, "فرمت زمان نامعتبر است.")
        else:
            messages.error(request, "تمام فیلدها الزامی هستند.")

    context = {
        'doctor': doctor,
        'availability': availability,
    }

    return render(request, 'doctors/edit_availability_day.html', context)


@login_required
def update_payment_settings(request):
    """بروزرسانی تنظیمات پرداخت پزشک"""
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')

    if request.method == 'POST':
        # دریافت جزئیات پرداخت از فرم
        account_name = request.POST.get('account_name', '')
        account_number = request.POST.get('account_number', '')
        bank_name = request.POST.get('bank_name', '')
        bank_branch = request.POST.get('bank_branch', '')
        payment_email = request.POST.get('payment_email', '')

        # بروزرسانی جزئیات پرداخت در پروفایل پزشک
        try:
            payment_details = doctor.payment_details
        except AttributeError:
            # اگر payment_details یک رابطه مدل واقعی نیست، می‌توان آن را به صورت متفاوتی مدیریت کرد
            doctor.payment_details = {
                'account_name': account_name,
                'account_number': account_number,
                'bank_name': bank_name,
                'bank_branch': bank_branch,
                'payment_email': payment_email
            }
            doctor.save()
            messages.success(request, "تنظیمات پرداخت با موفقیت بروزرسانی شد.")

    return redirect('doctors:doctor_earnings')



class DoctorMessageMixin(LoginRequiredMixin):
    """میکسین برای اطمینان از اینکه کاربر فعلی یک پزشک است"""

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'doctor'):
            messages.error(request, 'شما مجوز دسترسی به این صفحه را ندارید.')
            return redirect('doctors:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Email.objects.filter(
            recipient=self.request.user.doctor,
            is_read=False
        ).count()
        return context


class InboxView(DoctorMessageMixin, ListView):
    model = Email
    template_name = 'email/inbox.html'
    context_object_name = 'messages'
    paginate_by = 100

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')


        if search_query:
            queryset = queryset.filter(
                Q(tracking_number__icontains=search_query) |
                Q(subject__icontains=search_query) |
                Q(body__icontains=search_query) |
                Q(sender__user__first_name__icontains=search_query) |
                Q(sender__user__last_name__icontains=search_query)
            )
        return Email.objects.filter(
            recipient=self.request.user.doctor
        ).select_related(
            'sender__user',
            'sender__specialization'
        ).order_by('-is_read', '-sent_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


@require_GET
def doctor_search(request):
    query = request.GET.get('q', '')

    if not query:
        return JsonResponse({'results': []})

    doctors = Doctor.objects.filter(
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(specialization__title__icontains=query)
    ).select_related('user', 'specialization')[:10]

    results = [
        {
            'id': doctor.id,
            'name': doctor.user.get_full_name(),
            'specialization': doctor.specialization.title if doctor.specialization else '',
            'license': doctor.license_number,
            'image': doctor.profile_image.url if doctor.profile_image else ''
        }
        for doctor in doctors
    ]

    return JsonResponse({'results': results})


class SentMessagesView(DoctorMessageMixin, ListView):
    model = Email
    template_name = 'email/sent.html'
    context_object_name = 'messages'
    paginate_by = 10

    def get_queryset(self):
        return Email.objects.filter(
            sender=self.request.user.doctor
        ).select_related(
            'recipient__user',
            'recipient__specialization'
        ).order_by('-sent_at')


class ImportantMessagesView(DoctorMessageMixin, ListView):
    model = Email
    template_name = 'email/important.html'
    context_object_name = 'messages'
    paginate_by = 10

    def get_queryset(self):
        return Email.objects.filter(
            Q(recipient=self.request.user.doctor) & Q(is_important=True)
        ).select_related(
            'sender__user',
            'sender__specialization'
        ).order_by('-is_read', '-sent_at')


class MessageDetailView(DoctorMessageMixin, DetailView):
    model = Email
    template_name = 'email/detail.html'
    context_object_name = 'message'

    def get_queryset(self):
        return Email.objects.filter(
            Q(recipient=self.request.user.doctor) | Q(sender=self.request.user.doctor)
        ).select_related(
            'sender__user',
            'sender__specialization',
            'recipient__user',
            'recipient__specialization'
        )

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        message = self.object

        # اگر نامه برای کاربر فعلی است و خوانده نشده، آن را به عنوان خوانده شده علامت بزن
        if message.recipient == request.user.doctor and not message.is_read:
            message.is_read = True
            message.read_at = timezone.now()
            message.save()

        return response


class SendMessageView(DoctorMessageMixin, CreateView):
    model = Email
    form_class = EmailForm
    template_name = 'email/send.html'
    success_url = reverse_lazy('doctors:inbox')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_doctor'] = self.request.user.doctor
        return kwargs

    def form_valid(self, form):
        form.instance.sender = self.request.user.doctor
        response = super().form_valid(form)
        messages.success(self.request, 'نامه با موفقیت ارسال شد.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = EmailTemplate.objects.filter(doctor=self.request.user.doctor)
        return context


class ReplyMessageView(DoctorMessageMixin, CreateView):
    model = Email
    form_class = EmailForm
    template_name = 'email/reply.html'
    success_url = reverse_lazy('doctors:inbox')

    def get_initial(self):
        original_message = get_object_or_404(Email, pk=self.kwargs['pk'])
        return {
            'subject': f"پاسخ: {original_message.subject}",
            'recipient': original_message.sender,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['original_message'] = get_object_or_404(Email, pk=self.kwargs['pk'])
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_doctor'] = self.request.user.doctor
        return kwargs

    def form_valid(self, form):
        form.instance.sender = self.request.user.doctor
        form.instance.recipient = get_object_or_404(Email, pk=self.kwargs['pk']).sender
        response = super().form_valid(form)
        messages.success(self.request, 'پاسخ شما با موفقیت ارسال شد.')
        return response


class DeleteMessageView(DoctorMessageMixin, DeleteView):
    model = Email
    success_url = reverse_lazy('doctors:inbox')
    template_name = 'email/email_confirm_delete.html'

    def get_queryset(self):
        # کاربر فقط می‌تواند نامه‌های دریافتی یا ارسالی خود را حذف کند
        return Email.objects.filter(
            Q(recipient=self.request.user.doctor) | Q(sender=self.request.user.doctor)
        )

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'نامه با موفقیت حذف شد.')
        return super().delete(request, *args, **kwargs)


@login_required
def email_template_list(request):
    templates = request.user.doctor.email_templates.all()
    return render(request, 'email/email_template_list.html', {'templates': templates})

@login_required
def create_email_template(request):
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.doctor = request.user.doctor
            template.save()
            messages.success(request, "قالب با موفقیت ذخیره شد.")
            return redirect('doctors:email_template_list')
    else:
        form = EmailTemplateForm()
    return render(request, 'email/create_email_template.html', {'form': form})



@login_required
def update_doctor_location(request):
    """AJAX view to update doctor's geographic location"""
    if request.method == 'POST':
        try:
            doctor = request.user.doctor
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            
            if latitude and longitude:
                doctor.latitude = float(latitude)
                doctor.longitude = float(longitude)
                doctor.save(update_fields=['latitude', 'longitude'])
                
                return JsonResponse({
                    'success': True,
                    'message': 'موقعیت جغرافیایی با موفقیت بروزرسانی شد'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'مختصات جغرافیایی نامعتبر است'
                })
                
        except Doctor.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'پروفایل پزشک یافت نشد'
            })
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'مقادیر عرض و طول جغرافیایی نامعتبر است'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'درخواست نامعتبر'
    })

def test_fonts(request):
    """Test page for verifying IRANSansWeb fonts are loading correctly"""
    return render(request, 'test_fonts.html')

@login_required
def doctor_appointments_tabs(request):
    """نمایش نوبت‌های پزشک با قابلیت فیلتر و ایجاد نوبت همان روز"""
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')

    from datetime import datetime, date, timedelta
    from django.db.models import Q
    from patients.models import PatientsFile
    
    # Get filter parameters
    search = request.GET.get('search', '')
    date_filter = request.GET.get('date_filter', '')
    status_filter = request.GET.get('status_filter', '')
    
    # Base appointments query
    appointments = Reservation.objects.filter(
        doctor=doctor
    ).exclude(
        status='available'
    ).select_related(
        'patient', 'patient__user', 'day'
    ).order_by('-day__date', '-time')
    
    # Apply search filter
    if search:
        appointments = appointments.filter(
            Q(patient__user__first_name__icontains=search) |
            Q(patient__user__last_name__icontains=search) |
            Q(patient_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(patient_national_id__icontains=search)
        )
    
    # Apply date filter
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            appointments = appointments.filter(day__date=filter_date)
        except ValueError:
            pass
    
    # Apply status filter
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    # Get today's date
    today = date.today()
    
    # Separate appointments by time period
    today_appointments = appointments.filter(day__date=today)
    upcoming_appointments = appointments.filter(day__date__gt=today)[:10]
    past_appointments = appointments.filter(day__date__lt=today)[:10]
    
    # Get today's available time slots for same-day appointments
    today_available_slots = []
    try:
        today_reservation_day = ReservationDay.objects.get(
            doctor=doctor,
            date=today,
            is_available=True
        )
        
        # Get all reserved times for today
        reserved_times = Reservation.objects.filter(
            doctor=doctor,
            day=today_reservation_day
        ).exclude(
            status__in=['cancelled', 'available']
        ).values_list('time', flat=True)
        
        # Generate available time slots (assuming 30-minute intervals)
        from datetime import time
        current_time = today_reservation_day.start_time
        end_time = today_reservation_day.end_time
        
        while current_time < end_time:
            if current_time not in reserved_times:
                # Only show future time slots for today
                now = datetime.now().time()
                if current_time > now:
                    today_available_slots.append(current_time)
            
            # Add 30 minutes
            current_datetime = datetime.combine(today, current_time)
            current_datetime += timedelta(minutes=30)
            current_time = current_datetime.time()
            
    except ReservationDay.DoesNotExist:
        pass
    
    # Handle same-day appointment creation
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_same_day_appointment':
            patient_name = request.POST.get('patient_name')
            patient_phone = request.POST.get('patient_phone')
            appointment_time = request.POST.get('appointment_time')
            notes = request.POST.get('notes', '')
            
            if patient_name and patient_phone and appointment_time:
                try:
                    time_obj = datetime.strptime(appointment_time, '%H:%M').time()
                    
                    # Create or get patient file
                    patient_file, created = PatientsFile.objects.get_or_create(
                        phone=patient_phone,
                        defaults={
                            'name': patient_name,
                            'created_by_doctor': doctor
                        }
                    )
                    
                    # Create reservation
                    reservation = Reservation.objects.create(
                        doctor=doctor,
                        day=today_reservation_day,
                        time=time_obj,
                        patient=patient_file,
                        patient_name=patient_name,
                        phone=patient_phone,
                        notes=notes,
                        status='confirmed',  # Same-day appointments are auto-confirmed
                        created_by_doctor=True
                    )
                    
                    messages.success(request, f'نوبت همان روز برای {patient_name} در ساعت {appointment_time} ایجاد شد.')
                    
                    if created:
                        messages.info(request, f'پرونده جدید برای {patient_name} ایجاد شد.')
                    
                except ValueError:
                    messages.error(request, 'فرمت زمان نامعتبر است.')
                except Exception as e:
                    messages.error(request, f'خطا در ایجاد نوبت: {str(e)}')
            else:
                messages.error(request, 'لطفا تمام فیلدهای ضروری را پر کنید.')
        
        return redirect('doctors:doctor_appointments_tabs')
    
    # Prepare available patients for quick selection
    recent_patients = PatientsFile.objects.filter(
        reservation__doctor=doctor
    ).distinct().order_by('-updated_at')[:20]
    
    context = {
        'doctor': doctor,
        'today_appointments': today_appointments,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'today_available_slots': today_available_slots,
        'recent_patients': recent_patients,
        'search': search,
        'date_filter': date_filter,
        'status_filter': status_filter,
        'today_date': today,
    }

    return render(request, 'doctors/doctor_appointments.html', context)