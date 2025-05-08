from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Doctor, DoctorAvailability, Specialization, Clinic, City, DrComment, CommentTips
from reservations.models import Reservation, ReservationDay
from datetime import datetime, timedelta
from django.db.models import  Sum, Avg
from django.utils import timezone
from wallet.models import Transaction
from utils.utils import send_notification
from django.contrib import messages
from medimag.models import MagArticle
from docpages.models import Post
from django.shortcuts import render
from django.views.generic import ListView
from django.db.models import Q


def index(request):
    doctors = Doctor.objects.filter(is_available=True)
    clinics = Clinic.objects.all()
    specializations = Specialization.objects.all().order_by('name')
    articles = MagArticle.objects.all()
    context = {
        'doctors': doctors,
        'clinics': clinics,
        'specializations': specializations,
        'articles': articles,
    }
    return render(request, 'index/homepage.html', context)


def specializations(request):
    return render(request, 'doctors/specialization_list.html')


def explore(request):
    posts = Post.objects.filter(status='published')
    context = {
        'posts': posts,
    }
    return render(request, 'index/medexplore.html', context)



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
        if params['specialty'] and params['specialty'][0]:  # تغییر اینجا
            queryset = queryset.filter(specialization__name__in=params['specialty'])

            # فیلتر جنسیت
        if params['gender']:
            queryset = queryset.filter(gender=params['gender'])

            # فیلتر شهر - فقط اگر مقدار انتخاب شده باشد
        if params['city'] and params['city'][0]:  # تغییر اینجا
            queryset = queryset.filter(city__name__in=params['city'])

            # فیلتر کلینیک
        if params['clinic']:
            queryset = queryset.filter(clinic__name__icontains=params['clinic'])

            # فیلتر روزهای کاری - فقط اگر مقدار انتخاب شده باشد
        if params['days'] and params['days'][0]:  # تغییر اینجا
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
            queryset = queryset.order_by('next_available')

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
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.get_filter_params()

        context.update({
            'clinics': Clinic.objects.all(),
            'specializations': Specialization.objects.all().order_by('name'),
            'current_filters': params,
            'day_list': ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه'],
            'specialty': params['specialty'],
            'days': params['days'],
            'city_list': params['city'],
        })
        return context


def doctor_detail(request, pk):
    """نمایش اطلاعات کامل یک پزشک"""
    doctor = get_object_or_404(Doctor, pk=pk)

    # دریافت 7 روز آینده برای رزرو نوبت
    days = []
    today = datetime.now().date()
    comments = DrComment.objects.filter(doctor=doctor, status='confirmed')
    tips = CommentTips.objects.all()
    doctor.increment_view_count()
    posts = doctor.posts.filter(status='published')[:6]

    if request.method == 'POST':
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

    for i in range(7):
        day = today + timedelta(days=i)
        reservation_day, _ = ReservationDay.objects.get_or_create(date=day)

        if reservation_day.published:
            available_slots = doctor.get_available_slots(day)
            if available_slots:
                days.append({
                    'date': day,
                    'slots': available_slots
                })

    context = {
        'doctor': doctor,
        'days': days,
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

    # پرس و جوی پایه
    appointments = Reservation.objects.filter(doctor=doctor)

    # اعمال فیلترها
    if status != 'all':
        appointments = appointments.filter(status=status)

    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            appointments = appointments.filter(day__date__gte=date_from)
        except ValueError:
            pass

    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            appointments = appointments.filter(day__date__lte=date_to)
        except ValueError:
            pass

    # مرتب‌سازی بر اساس تاریخ و زمان
    appointments = appointments.order_by('day__date', 'time')

    context = {
        'doctor': doctor,
        'appointments': appointments,
        'status': status,
        'date_from': date_from,
        'date_to': date_to,
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

                # ایجاد روز جدید در زمان‌بندی
                availability = DoctorAvailability.objects.create(
                    doctor=doctor,
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time
                )
                messages.success(request, "زمان‌بندی جدید با موفقیت افزوده شد.")
                return redirect('doctors:doctor_availability')
            except ValueError:
                messages.error(request, "فرمت روز نامعتبر است.")
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
        return redirect('doctors:doctor_list')

    if request.method == 'POST':
        consultation_fee = request.POST.get('consultation_fee')
        consultation_duration = request.POST.get('consultation_duration')

        if consultation_fee and consultation_duration:
            try:
                doctor.consultation_fee = float(consultation_fee)
                doctor.consultation_duration = int(consultation_duration)
                doctor.save()
                messages.success(request, "تنظیمات با موفقیت بروزرسانی شد.")
            except ValueError:
                messages.error(request, "مقادیر وارد شده نامعتبر هستند.")
        else:
            messages.error(request, "تمام فیلدها الزامی هستند.")

    return redirect('doctors:doctor_availability')


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
