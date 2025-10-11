from django.db.models import Max
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from .forms import ContactForm
from .models import SupportChatRoom, SupportMessage
from django.contrib.auth import get_user_model

User = get_user_model()


def is_user_admin(user):
    return user.is_authenticated and getattr(user, 'is_admin_chat', False)


def chat_room_list(request):
    """
    نمایش لیست چت‌ها:
    - ادمین: همه چت‌های فعال
    - کاربر لاگین‌شده: فقط چت خودش
    - مهمان: چت موجود در سشن
    """
    if is_user_admin(request.user):
        chats = SupportChatRoom.objects.filter(
            is_active=True
        ).select_related('customer').annotate(
            last_message_time=Max('messages__created_at')
        ).order_by('-last_message_time')
    else:
        return redirect('/')

    return render(request, 'support/room_list.html', {
        'chats': chats,
        'is_admin': is_user_admin(request.user)
    })


def create_auto_chat_room(request):
    """
    ساخت چت جدید:
    - ادمین‌ها هدایت می‌شن به لیست چت
    - کاربر لاگین‌شده به عنوان customer ذخیره میشه
    - مهمان: بدون یوزر، ID چت در session ذخیره میشه
    """
    if is_user_admin(request.user):
        return redirect('support:chat_room_list')

    if request.user.is_authenticated:
        chat_room = SupportChatRoom.objects.create(customer=request.user)
    else:
        chat_room = SupportChatRoom.objects.create()
        request.session['chat_room_id'] = chat_room.id

    return redirect('support:chat_room', room_id=chat_room.id)


def chat_room(request, room_id):
    """
    نمایش یک چت خاص بر اساس دسترسی:
    - ادمین: دسترسی به همه چت‌ها
    - کاربر: فقط چت خودش
    - مهمان: فقط چت سشن
    """
    chat_room = get_object_or_404(SupportChatRoom, id=room_id)

    if is_user_admin(request.user):
        pass  # دسترسی کامل
    elif request.user.is_authenticated:
        if chat_room.customer != request.user:
            return redirect('support:chat_room_list')
    else:
        if request.session.get('chat_room_id') != chat_room.id:
            return redirect('support:create_auto_chat_room')

    messages = chat_room.messages.all().select_related('sender').order_by('created_at')

    return render(request, 'support/chat_room.html', {
        'chat_room': chat_room,
        'messages': messages,
        'is_admin': is_user_admin(request.user)
    })


def send_message(request, room_id):
    """
    ارسال پیام در چت:
    - فقط وقتی دسترسی مجاز باشه
    - ناشناس‌ها فقط برای چت سشن خودشون
    """
    chat_room = get_object_or_404(SupportChatRoom, id=room_id)
    sender = request.user if request.user.is_authenticated else None

    if is_user_admin(request.user):
        pass
    elif request.user.is_authenticated:
        if chat_room.customer != request.user:
            return JsonResponse({'error': 'Access denied'}, status=403)
    else:
        if request.session.get('chat_room_id') != chat_room.id:
            return JsonResponse({'error': 'Access denied'}, status=403)

    content = request.POST.get('content')
    if not content:
        return JsonResponse({'error': 'No content provided'}, status=400)

    SupportMessage.objects.create(
        chat_room=chat_room,
        sender=sender,
        content=content
    )

    return JsonResponse({'status': 'success'})

def get_chat_messages(request):
    if request.user.is_authenticated:
        room = SupportChatRoom.objects.filter(customer=request.user).first()
    else:
        chat_room_id = request.session.get('chat_room_id')
        if chat_room_id:
            room = SupportChatRoom.objects.filter(id=chat_room_id).first()
        else:
            room = None

    if not room:
        return JsonResponse({'messages': []})

    messages = SupportMessage.objects.filter(chat_room=room).order_by('created_at').select_related('sender')

    formatted_messages = []
    for msg in messages:
        if msg.sender is None:
            sender_name = 'سیستم'
            sender_is_admin = False
        else:
            sender_is_admin = getattr(msg.sender, 'is_admin', False)
            sender_name = 'ادمین' if sender_is_admin else 'شما'

        formatted_messages.append({
            'content': msg.content,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M'),
            'sender_name': sender_name,
            'sender_is_admin': sender_is_admin
        })

    return JsonResponse({'messages': formatted_messages})



def page_not_found(request):
    return render(request, 'about_us/404.html')

def about_us(request):
    return render(request, 'about_us/about_us.html')

def for_doctors(request):
    return render(request, 'reservations/payment_choice.html')

def frequently(request):
    return render(request, 'about_us/frequently.html')

def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'پیام شما با موفقیت برای ما ارسال شد! ممنونیم که وقت گذاشتید :)')
            return redirect('support:contact_us')
    else:
        form = ContactForm()
    return render(request, 'about_us/contact_us.html', {'form': form})
