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
from django.views.decorators.http import require_POST
"""

TO DO : Connecting the chat request to the wallet like an 
appointment system (one step before submitting the request is also necessary).
"""


@login_required
@require_POST
def request_chat(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if hasattr(request.user, 'doctor'):
        messages.error(request, 'فقط بیماران می‌توانند درخواست چت ارسال کنند')
        return redirect('doctors:index')
    else:
        patient = request.user.patient
        existing_active_request = ChatRequest.objects.filter(Q(status='pending') | Q(status='approved'),patient=patient, doctor=doctor,).last()
        if existing_active_request:
            messages.info(request, 'شما یک درخواست فعال با پزشک مورد نظر دارید!')
            return redirect('chat:request_status', request_id=existing_active_request.id)
    
    user = request.user
    patient_name = request.POST.get('patient_name', '').strip()
    patient_last_name = request.POST.get('patient_last_name', '').strip()
    patient_national_id = request.POST.get('patient_national_id', '').strip()
    disease_summary = request.POST.get('disease_summary', '').strip()
    phone = request.POST.get('phone', user.phone if hasattr(user, 'phone') else '').strip()
    
    # Update user information
    user.first_name = patient_name
    user.last_name = patient_last_name
    user.save()
    
    if patient_national_id:
        user.patient.national_id = patient_national_id
        user.patient.save()

    # Create chat request with payment information
    consultation_fee = doctor.online_visit_fee
    full_name = f"{patient_name} {patient_last_name}".strip()
    
    new_request = ChatRequest.objects.create(
        patient=patient, 
        doctor=doctor,
        disease_summary=disease_summary,
        amount=consultation_fee,
        patient_name=full_name,
        patient_national_id=patient_national_id,
        phone=phone
    )
    
    # Check payment method preference
    payment_method = request.POST.get('payment_method', 'wallet')
    
    if payment_method == 'direct':
        # Direct payment booking
        success, message = new_request.request_with_direct_payment(user)
        
        if success:
            # Redirect to payment page
            return redirect('payments:chat_payment', chat_request_id=new_request.id)
        else:
            new_request.delete()
            messages.error(request, message)
            return redirect('chat:list_doctors')
    else:
        # Wallet payment booking
        success, message = new_request.process_payment(user)
        
        if success:
            messages.success(request, f'درخواست چت با موفقیت ثبت شد. {message}')
            return redirect('chat:request_status', request_id=new_request.id)
        else:
            # Don't delete the request yet - store for payment choice
            messages.error(request, message)
            
            # If insufficient balance, redirect to payment choice
            if "موجودی کیف پول کافی نیست" in message:
                from wallet.models import Wallet
                from django.urls import reverse
                
                # Store request data in session for payment choice
                request.session['pending_chat_data'] = {
                    'chat_request_id': new_request.id,
                    'doctor_id': doctor_id,
                }
                
                # Redirect to payment choice page
                return redirect('chat:payment_choice', chat_request_id=new_request.id)
            
            # Delete the request if other error
            new_request.delete()
            return redirect('chat:list_doctors')


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
        # Check if payment has been made
        if chat_request.payment_status != 'paid':
            return JsonResponse({'status': 'error', 'message': 'پرداخت انجام نشده است'}, status=400)
        
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
        
        # Process refund if payment was made
        if chat_request.payment_status == 'paid' and chat_request.transaction:
            from wallet.models import Transaction
            try:
                Transaction.objects.create(
                    user=chat_request.transaction.user,
                    wallet=chat_request.transaction.wallet,
                    amount=chat_request.amount,
                    transaction_type='refund',
                    payment_method='wallet',
                    status='completed',
                    description=f'بازپرداخت مشاوره رد شده - دکتر {chat_request.doctor.user.get_full_name()}',
                    related_transaction=chat_request.transaction,
                    metadata={
                        'chat_request_id': chat_request.id,
                        'refund_reason': 'doctor_rejection'
                    }
                )
                # Update wallet balance
                chat_request.transaction.wallet.add_balance(chat_request.amount)
                chat_request.payment_status = 'refunded'
                chat_request.save()
            except Exception as e:
                # Log error but don't prevent rejection
                pass
        
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
    paginate_by = 10  # Show 10 doctors per page


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

        # Get user's wallet balance if authenticated
        balance = 0
        if self.request.user.is_authenticated:
            from wallet.models import Wallet
            wallet, created = Wallet.objects.get_or_create(user=self.request.user)
            balance = wallet.balance

        context.update({
            'specializations': Specialization.objects.all().order_by('name'),
            'supplementary_list': params['supplementary'],
            'current_filters': params,
            'specialty': params['specialty'],
            'available_doctors': Doctor.objects.filter(availability__is_available=True).select_related('user'),
            'balance': balance,
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


@login_required
def payment_choice(request, chat_request_id):
    """انتخاب روش پرداخت برای مشاوره آنلاین"""
    try:
        chat_request = ChatRequest.objects.get(
            id=chat_request_id,
            patient=request.user.patient,
            payment_status='pending'
        )
    except ChatRequest.DoesNotExist:
        messages.error(request, 'درخواست مورد نظر یافت نشد')
        return redirect('chat:list_doctors')
    
    # Get user's wallet
    from wallet.models import Wallet
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Calculate amounts
    required_amount = chat_request.amount
    current_balance = wallet.balance
    needed_amount = max(0, required_amount - current_balance)
    
    # Calculate suggested deposit amount
    suggested_amount = int(needed_amount * 1.1)
    suggested_amount = ((suggested_amount + 9999) // 10000) * 10000
    suggested_amount = max(10000, suggested_amount)
    
    context = {
        'chat_request': chat_request,
        'wallet': wallet,
        'required_amount': required_amount,
        'current_balance': current_balance,
        'needed_amount': needed_amount,
        'suggested_amount': suggested_amount,
    }
    
    return render(request, 'chat/payment_choice.html', context)


@login_required
def process_payment_choice(request, chat_request_id):
    """پردازش انتخاب روش پرداخت"""
    if request.method != 'POST':
        return redirect('chat:payment_choice', chat_request_id=chat_request_id)
    
    payment_choice = request.POST.get('payment_choice')
    
    if payment_choice == 'wallet_charge':
        # Redirect to wallet deposit
        from django.urls import reverse
        suggested_amount = request.POST.get('suggested_amount', '10000')
        return redirect(f"{reverse('wallet:deposit')}?amount={suggested_amount}&redirect_to={reverse('chat:payment_choice', args=[chat_request_id])}")
    
    elif payment_choice == 'direct_payment':
        # Get pending chat data from session
        pending_data = request.session.get('pending_chat_data', {})
        
        if not pending_data or pending_data.get('chat_request_id') != int(chat_request_id):
            messages.error(request, 'اطلاعات درخواست یافت نشد. لطفاً دوباره تلاش کنید.')
            return redirect('chat:list_doctors')
        
        try:
            chat_request = ChatRequest.objects.get(id=chat_request_id, patient=request.user.patient)
            
            # Update to direct payment
            success, message = chat_request.request_with_direct_payment(request.user)
            
            if success:
                # Clear session data
                if 'pending_chat_data' in request.session:
                    del request.session['pending_chat_data']
                
                # Redirect to payment page
                return redirect('payments:chat_payment', chat_request_id=chat_request.id)
            else:
                messages.error(request, message)
                return redirect('chat:payment_choice', chat_request_id=chat_request_id)
                
        except ChatRequest.DoesNotExist:
            messages.error(request, 'درخواست مورد نظر یافت نشد')
            return redirect('chat:list_doctors')
    
    else:
        messages.error(request, 'انتخاب نامعتبر')
        return redirect('chat:payment_choice', chat_request_id=chat_request_id)