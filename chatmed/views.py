from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from txaio.aio import reject
from .models import ChatRequest, ChatRoom, Message, DoctorAvailability
from doctors.models import Doctor, Specialization
from patients.models import PatientsFile as Patient
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.generic import ListView
from django.db.models import Q, Avg

"""
TO DO : Connecting the chat request to the wallet like an 
appointment system (one step before submitting the request is also necessary).
"""


@login_required
def request_chat(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if not hasattr(request.user, 'patient'):
        messages.error(request, 'فقط بیماران می‌توانند درخواست چت ارسال کنند')
        return redirect('doctors:index')

    patient = request.user.patient
    existing_active_request = ChatRequest.objects.filter(Q(status='pending') | Q(status='approved'),patient=patient, doctor=doctor,).last()
    if existing_active_request:
        messages.info(request, 'شما یک درخواست فعال با پزشک مورد نظر دارید!')
        return redirect('chat:request_status', request_id=existing_active_request.id)

    new_request = ChatRequest.objects.create(patient=patient, doctor=doctor)
    messages.success(request, 'درخواست چت با موفقیت ثبت شد')
    return redirect('chat:request_status', request_id=new_request.id)


@login_required
def request_status(request, request_id):
    chat_request = get_object_or_404(ChatRequest, id=request_id)

    if hasattr(request.user, 'patient') and chat_request.patient != request.user.patient:
        raise PermissionDenied
    elif hasattr(request.user, 'doctor') and chat_request.doctor != request.user.doctor:
        raise PermissionDenied

    return render(request, 'chat/status_request.html', {'request': chat_request})


@login_required
def manage_chat_request(request, request_id, action):
    chat_request = get_object_or_404(ChatRequest, id=request_id, doctor__user=request.user)

    if action == 'approve':
        chat_request.status = ChatRequest.APPROVED
        chat_request.save()

        chat_room, created = ChatRoom.objects.get_or_create(
            request=chat_request,
            defaults={'is_active': True}
        )

        return JsonResponse({'status': 'approved', 'room_id': chat_room.id})

    elif action == 'reject':
        chat_request.status = ChatRequest.REJECTED
        chat_request.save()
        return JsonResponse({'status': 'rejected'})

    elif action == "finished":
        chat_request.status = ChatRequest.FINISHED
        chat_request.chat_room.is_active = False
        chat_request.chat_room.save()
        chat_request.save()
        return JsonResponse({"status": "finished"})

    return JsonResponse({'status': 'error', 'message': 'عملیات نامعتبر'}, status=400)


@login_required
def chat_room_list(request):
    if hasattr(request.user, 'doctor'):
        chat_rooms = ChatRoom.objects.filter(
            request__doctor=request.user.doctor,
            is_active=True
        ).select_related('request', 'request__patient').order_by('-last_activity')

        finished_chats = ChatRoom.objects.filter(
            request__doctor=request.user.doctor,
            is_active=False
        ).select_related('request', 'request__patient').order_by('-last_activity')

        reject_requests = ChatRequest.objects.filter(
            doctor=request.user.doctor,
            status=ChatRequest.REJECTED
        ).select_related('patient__user')

        pending_requests = ChatRequest.objects.filter(
            doctor=request.user.doctor,
            status=ChatRequest.PENDING
        ).select_related('patient__user')

        return render(request, 'chat/doctor_chat_list.html', {
            'chat_rooms': chat_rooms,
            'pending_requests': pending_requests,
            'reject_requests': reject_requests,
            'finished_chats': finished_chats,
            'doctor': request.user.doctor,
        })

    elif hasattr(request.user, 'patient'):
        chat_rooms = ChatRoom.objects.filter(
            request__patient=request.user.patient,
            is_active=True
        ).select_related('request', 'request__doctor').order_by('-last_activity')

        finished_chats = ChatRoom.objects.filter(
            request__patient=request.user.patient,
            is_active=False
        )

        pending_chats = ChatRequest.objects.filter(
            patient=request.user.patient,
            status=ChatRequest.PENDING
        )

        reject_chats = ChatRequest.objects.filter(
            patient=request.user.patient,
            status=ChatRequest.REJECTED
        )

        return render(request, 'chat/patients_list_chat.html', {
            'chat_rooms': chat_rooms,
            'finished_chats': finished_chats,
            'pending_chats': pending_chats,
            'reject_chats': reject_chats,
        })

    messages.error(request, "شما مجاز به مشاهده لیست چت‌ها نیستید.")
    return redirect('chat:chat_home')




@login_required
def chat_room(request, room_id):
    chat_room = get_object_or_404(ChatRoom, id=room_id)

    # چک دسترسی بر اساس نوع کاربر و شناسه‌ها
    if hasattr(request.user, 'doctor'):
        if chat_room.request.doctor.id != request.user.doctor.id:
            return HttpResponseForbidden("دسترسی غیرمجاز")
    elif hasattr(request.user, 'patient'):
        if chat_room.request.patient.id != request.user.patient.id:
            return HttpResponseForbidden("دسترسی غیرمجاز")
    else:
        # اگر کاربر نه دکتر است نه بیمار، دسترسی ندارد
        return HttpResponseForbidden("دسترسی غیرمجاز")

    # اگر دکتر است، پیام‌های خوانده نشده توسط خودش را به عنوان خوانده شده علامت بزن
    if hasattr(request.user, 'doctor'):
        chat_room.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    messages_qs = chat_room.messages.all().select_related('sender').order_by('created_at')

    return render(request, 'chat/chat_room.html', {
        'chat_room': chat_room,
        'messages': messages_qs,
        'is_doctor': hasattr(request.user, 'doctor')
    })
@require_POST
@login_required
def send_message(request, room_id):
    chat_room = get_object_or_404(ChatRoom, id=room_id)

    if hasattr(request.user, 'doctor') and chat_room.request.doctor != request.user.doctor:
        return JsonResponse({'status': 'error', 'message': 'دسترسی غیرمجاز'}, status=403)
    elif hasattr(request.user, 'patient') and chat_room.request.patient != request.user.patient:
        return JsonResponse({'status': 'error', 'message': 'دسترسی غیرمجاز'}, status=403)

    content = request.POST.get('content', '').strip()
    message_type = request.POST.get('message_type', 'text')
    file = request.FILES.get('file')
    audio = request.FILES.get('audio')

    if message_type == 'text' and not content:
        return JsonResponse({'status': 'error', 'message': 'متن پیام نمی‌تواند خالی باشد'}, status=400)

    message = Message.objects.create(
        chat_room=chat_room,
        sender=request.user,
        content=content if message_type == 'text' else '',
        file=file if message_type == 'file' else None,
        audio=audio if message_type == 'audio' else None,
        message_type=message_type
    )

    chat_room.last_activity = timezone.now()
    chat_room.save()

    return JsonResponse({
        'status': 'success',
        'message_id': message.id,
        'created_at': message.created_at.strftime('%Y-%m-%d %H:%M'),
        'message_type': message_type,
        'file_url': message.file.url if message.file else None,
        'audio_url': message.audio.url if message.audio else None
    })


@login_required
def toggle_availability(request):
    if not hasattr(request.user, 'doctor'):
        return JsonResponse({'status': 'error', 'message': 'فقط پزشکان می‌توانند وضعیت را تغییر دهند'}, status=403)

    availability, _ = DoctorAvailability.objects.get_or_create(doctor=request.user.doctor)
    availability.is_available = not availability.is_available
    availability.save()

    return JsonResponse({
        'status': 'success',
        'is_available': availability.is_available
    })





class OnDoctorListView(ListView):
    model = Doctor
    template_name = 'chat/online_doctors.html'
    context_object_name = 'doctors'


    def get_queryset(self):
        queryset = super().get_queryset().filter(is_available=True,online_visit=True)
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


        if params['supplementary'] and params['supplementary'][0]:
                queryset = queryset.filter(Insurance__name__in=params['supplementary'])

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
        elif params['sort'] == 'پزشکان آنلاین':
            queryset = queryset.order_by('-availability__is_available')

        return queryset

    def get_filter_params(self):
        return {
            'query': self.request.GET.get('query', ''),
            'specialty': self.request.GET.getlist('specialty'),
            'sort': self.request.GET.get('sort', ''),
            'supplementary': self.request.GET.getlist('supplementary')
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.get_filter_params()

        context.update({
            'specializations': Specialization.objects.all().order_by('name'),
            'supplementary_list': params['supplementary'],
            'current_filters': params,
            'specialty': params['specialty'],
            'available_doctors': Doctor.objects.filter(availability__is_available=True).select_related('user'),

        })
        return context





@require_POST
@login_required
def close_chat(request, room_id):
    chat_room = get_object_or_404(ChatRoom, id=room_id)

    if not hasattr(request.user, 'doctor') or chat_room.request.doctor != request.user.doctor:
        return JsonResponse({'status': 'error', 'message': 'شما مجاز به پایان دادن این چت نیستید'}, status=403)

    reason = request.POST.get('reason', '')

    try:
        chat_room.close_chat(request.user, reason)
        return JsonResponse({'status': 'success', 'message': 'چت با موفقیت پایان یافت'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def manage_chat(request):
    if request.user.is_authenticated:
        if getattr(request.user, 'doctor', None) or getattr(request.user, 'patient', None):
            return redirect('chat:chat_room_list')

    else:
        return redirect('chat:list_doctors')




@csrf_exempt
def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        file_path = default_storage.save(f'uploads/{uploaded_file.name}', ContentFile(uploaded_file.read()))
        file_url = default_storage.url(file_path)
        return JsonResponse({'file_url': file_url})
    return JsonResponse({'error': 'Invalid request'}, status=400)