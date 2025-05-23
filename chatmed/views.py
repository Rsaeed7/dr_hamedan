from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import ChatRequest, ChatRoom, Message, DoctorAvailability
from doctors.models import Doctor
from patients.models import PatientsFile as Patient



@login_required
def request_chat(request, doctor_id):
    """
    بیمار درخواست چت با پزشک را ارسال می‌کند
    و به صفحه وضعیت هدایت می‌شود
    """
    doctor = get_object_or_404(Doctor, id=doctor_id)

    if not hasattr(request.user, 'patient'):
        messages.error(request, 'فقط بیماران می‌توانند درخواست چت ارسال کنند')
        return redirect('home')

    patient = request.user.patient

    # بررسی وجود درخواست قبلی
    existing_request = ChatRequest.objects.filter(
        patient=patient,
        doctor=doctor
    ).first()

    if existing_request:
        messages.info(request, 'شما قبلاً برای این پزشک درخواست ارسال کرده‌اید')
        return redirect('chat:request_status', request_id=existing_request.id)

    # ایجاد درخواست جدید
    new_request = ChatRequest.objects.create(
        patient=patient,
        doctor=doctor
    )

    messages.success(request, 'درخواست چت با موفقیت ثبت شد')
    return redirect('chat:request_status', request_id=new_request.id)


@login_required
def request_status(request, request_id):
    """نمایش وضعیت درخواست چت"""
    chat_request = get_object_or_404(ChatRequest, id=request_id)

    # بررسی مالکیت درخواست
    if hasattr(request.user, 'patient'):
        if chat_request.patient != request.user.patient:
            raise PermissionDenied
    elif hasattr(request.user, 'doctor'):
        if chat_request.doctor != request.user.doctor:
            raise PermissionDenied
    else:
        raise PermissionDenied

    return render(request, 'chat/status_request.html', {
        'request': chat_request
    })


@login_required
def manage_chat_request(request, request_id, action):
    """
    پزشک درخواست چت را مدیریت می‌کند (تایید/رد)
    """
    chat_request = get_object_or_404(ChatRequest, id=request_id, doctor__user=request.user)

    if action == 'approve':
        chat_request.status = ChatRequest.APPROVED
        chat_request.save()

        # ایجاد اتاق چت
        chat_room, created = ChatRoom.objects.get_or_create(
            request=chat_request,
            defaults={'is_active': True}
        )

        return JsonResponse({
            'status': 'approved',
            'room_id': chat_room.id
        })

    elif action == 'reject':
        chat_request.status = ChatRequest.REJECTED
        chat_request.save()
        return JsonResponse({'status': 'rejected'})

    return JsonResponse({'status': 'error', 'message': 'عملیات نامعتبر'}, status=400)


@login_required
def chat_room_list(request):
    """
    نمایش لیست چت‌های فعال برای کاربر جاری
    """
    if hasattr(request.user, 'doctor'):
        # برای پزشکان: نمایش چت‌های تایید شده
        chat_rooms = ChatRoom.objects.filter(
            request__doctor=request.user.doctor,
            is_active=True
        ).select_related('request__patient').order_by('-last_activity')

        # نمایش درخواست‌های در انتظار
        pending_requests = ChatRequest.objects.filter(
            doctor=request.user.doctor,
            status=ChatRequest.PENDING
        ).select_related('patient__user')

        return render(request, 'chat/doctor_chat_list.html', {
            'chat_rooms': chat_rooms,
            'pending_requests': pending_requests
        })

    elif hasattr(request.user, 'patient'):
        # برای بیماران: نمایش چت‌های تایید شده
        chat_rooms = ChatRoom.objects.filter(
            request__patient=request.user.patient,
            is_active=True
        ).select_related('request__doctor').order_by('-last_activity')

        return render(request, 'chat/patients_list_chat.html', {
            'chat_rooms': chat_rooms
        })

    return redirect('chat:chat_home')


@login_required
def chat_room(request, room_id):
    """
    نمایش اتاق چت و پیام‌ها
    """
    chat_room = get_object_or_404(ChatRoom, id=room_id)

    # بررسی دسترسی کاربر
    if hasattr(request.user, 'doctor'):
        if chat_room.request.doctor != request.user.doctor:
            return JsonResponse({'status': 'error', 'message': 'دسترسی غیرمجاز'}, status=403)
    elif hasattr(request.user, 'patient'):
        if chat_room.request.patient != request.user.patient:
            return JsonResponse({'status': 'error', 'message': 'دسترسی غیرمجاز'}, status=403)
    else:
        return JsonResponse({'status': 'error', 'message': 'دسترسی غیرمجاز'}, status=403)

    # علامت گذاری پیام‌ها به عنوان خوانده شده
    if hasattr(request.user, 'doctor'):
        chat_room.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    messages = chat_room.messages.all().select_related('sender').order_by('created_at')

    return render(request, 'chat/chat_room.html', {
        'chat_room': chat_room,
        'messages': messages,
        'is_doctor': hasattr(request.user, 'doctor')
    })


@require_POST
@login_required
def send_message(request, room_id):
    """
    ارسال پیام جدید در چت
    """
    chat_room = get_object_or_404(ChatRoom, id=room_id)

    # بررسی دسترسی کاربر
    if hasattr(request.user, 'doctor'):
        if chat_room.request.doctor != request.user.doctor:
            return JsonResponse({'status': 'error', 'message': 'دسترسی غیرمجاز'}, status=403)
    elif hasattr(request.user, 'patient'):
        if chat_room.request.patient != request.user.patient:
            return JsonResponse({'status': 'error', 'message': 'دسترسی غیرمجاز'}, status=403)
    else:
        return JsonResponse({'status': 'error', 'message': 'دسترسی غیرمجاز'}, status=403)

    content = request.POST.get('content', '').strip()

    if not content:
        return JsonResponse({'status': 'error', 'message': 'متن پیام نمی‌تواند خالی باشد'}, status=400)

    # ایجاد پیام جدید
    message = Message.objects.create(
        chat_room=chat_room,
        sender=request.user,
        content=content
    )

    # به‌روزرسانی زمان آخرین فعالیت
    chat_room.last_activity = timezone.now()
    chat_room.save()

    return JsonResponse({
        'status': 'success',
        'message_id': message.id,
        'created_at': message.created_at.strftime('%Y-%m-%d %H:%M')
    })


@login_required
def toggle_availability(request):
    """
    تغییر وضعیت دسترسی پزشک برای چت
    """
    if not hasattr(request.user, 'doctor'):
        return JsonResponse({'status': 'error', 'message': 'فقط پزشکان می‌توانند وضعیت را تغییر دهند'}, status=403)

    availability, created = DoctorAvailability.objects.get_or_create(
        doctor=request.user.doctor
    )
    availability.is_available = not availability.is_available
    availability.save()

    return JsonResponse({
        'status': 'success',
        'is_available': availability.is_available
    })



def home(request):
    # اگر کاربر لاگین کرده باشد
    if request.user.is_authenticated:
        # اگر پزشک است
        if getattr(request.user, 'doctor', None):
            return redirect('chat:chat_room_list')
        # اگر بیمار است
        elif getattr(request.user, 'patient', None):
            return redirect('chat:chat_room_list')

    # اگر کاربر لاگین نکرده باشد
    return render(request, 'chat/home.html', {
        'doctors': Doctor.objects.filter(availability__is_available=True)
    })


# from django.contrib.auth.decorators import login_required
# from django.shortcuts import redirect, render
# from doctors.models import Doctor

@login_required
def list_doctors(request):
    """List available doctors for patients with filters"""
    if not getattr(request.user, 'patient', None):
        return redirect('home')

    available_doctors = Doctor.objects.filter(
        availability__is_available=True
    ).select_related('user')

    params = request.GET

    # **فیلتر بر اساس تخصص (specialty)**
    if 'specialty' in params and params['specialty']:
        available_doctors = available_doctors.filter(specialization__name__in=params.getlist('specialty'))

    # **مرتب‌سازی بر اساس معیار انتخاب شده (sort)**
    sort_options = {
        'پر بازدیدترین': '-view_count',
        'بالاترین امتیاز': '-avg_comment_rating',
        'نزدیک‌ترین نوبت خالی': 'next_available'
    }
    if 'sort' in params and params['sort'] in sort_options:
        available_doctors = available_doctors.order_by(sort_options[params['sort']])

    return render(request, 'chat/online_doctors.html', {
        'doctors': available_doctors
    })


@require_POST
@login_required
def close_chat(request, room_id):
    chat_room = get_object_or_404(ChatRoom, id=room_id)

    # بررسی اینکه کاربر پزشک است
    if not hasattr(request.user, 'doctor') or chat_room.request.doctor != request.user.doctor:
        return JsonResponse({'status': 'error', 'message': 'شما مجاز به پایان دادن این چت نیستید'}, status=403)

    reason = request.POST.get('reason', '')

    try:
        chat_room.close_chat(request.user, reason)
        return JsonResponse({'status': 'success', 'message': 'چت با موفقیت پایان یافت'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)