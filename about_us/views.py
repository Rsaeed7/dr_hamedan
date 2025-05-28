from django.shortcuts import render,redirect
from .forms import ContactForm
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import SupportChatRoom, SupportMessage

def is_user_admin(user):
    return user.is_authenticated and user.is_admin_chat

def user_is_admin_of_chat(user, chat_room):
    return is_user_admin(user) and chat_room.admins.filter(id=user.id).exists()

def user_is_customer_of_chat(user, chat_room):
    return user.is_authenticated and chat_room.customer == user

def can_access_chat(user, chat_room, session):
    if user_is_admin_of_chat(user, chat_room):
        return True
    if user_is_customer_of_chat(user, chat_room):
        return True
    if not user.is_authenticated and session.get('chat_room_id') == chat_room.id:
        return True
    return False


def chat_room_list(request):
    if is_user_admin(request.user):
        # فقط چت‌هایی که ادمین‌ها بهش اختصاص دارن
        chats = SupportChatRoom.objects.filter(
            is_active=True,
            admins=request.user
        ).select_related('customer').order_by('-last_activity')
    elif request.user.is_authenticated:
        chats = SupportChatRoom.objects.filter(
            is_active=True,
            customer=request.user
        ).select_related('customer').order_by('-last_activity')
    else:
        chat_room_id = request.session.get('chat_room_id')
        if chat_room_id:
            chats = SupportChatRoom.objects.filter(id=chat_room_id, is_active=True)
        else:
            chats = SupportChatRoom.objects.none()

    return render(request, 'support/room_list.html', {
        'chats': chats,
        'is_admin': is_user_admin(request.user)
    })


def create_auto_chat_room(request):
    if is_user_admin(request.user):
        return redirect('about:chat_room_list')

    if request.user.is_authenticated:
        chat_room = SupportChatRoom.objects.create(customer=request.user)
    else:
        chat_room = SupportChatRoom.objects.create()  # customer = null

    # در صورت نیاز ادمین‌ها را بعدا اضافه کن، مثلا ادمین پیشفرض
    # chat_room.admins.add(default_admin_user)

    if not request.user.is_authenticated:
        request.session['chat_room_id'] = chat_room.id

    return redirect('about:chat_room', room_id=chat_room.id)


def chat_room(request, room_id):
    chat_room = get_object_or_404(SupportChatRoom, id=room_id)

    if not can_access_chat(request.user, chat_room, request.session):
        if not request.user.is_authenticated:
            # ناشناس‌ها به صفحه ایجاد چت هدایت شوند
            return redirect('about:create_auto_chat_room')
        return redirect('about:chat_room_list')

    messages = chat_room.messages.all().select_related('sender').order_by('created_at')

    return render(request, 'support/chat_room.html', {
        'chat_room': chat_room,
        'messages': messages,
        'is_admin': is_user_admin(request.user)
    })


def send_message(request, room_id):
    chat_room = get_object_or_404(SupportChatRoom, id=room_id)
    sender = request.user if request.user.is_authenticated else None

    if not can_access_chat(request.user, chat_room, request.session):
        return JsonResponse({'error': 'Access denied'}, status=403)

    content = request.POST.get('content')
    if not content:
        return JsonResponse({'error': 'No content provided'}, status=400)

    SupportMessage.objects.create(
        chat_room=chat_room,
        sender=sender,
        content=content,
        # اضافه کردن فیلد is_admin_message اگر لازمه
    )
    return JsonResponse({'status': 'success'})


# این فانکشن برای تست صفحه 404 میباشد و روی سرور کاربرد ندارد
def page_not_found(request):
    return render(request, 'about_us/404.html')


def about_us(request):
    return render(request, 'about_us/about_us.html')

def for_doctors(request):
    return render(request, 'about_us/for_doctors.html')



def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,'پیام شما با موفقیت برای ما ارسال شد! ممنونیم که وقت گذاشتید:)')
            return redirect('about:contact_us')
    else:
        form = ContactForm()
    return render(request,'about_us/contact_us.html',{'form':form})
