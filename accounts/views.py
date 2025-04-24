# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from django.db import transaction

from .models import UserProfile
from .forms import RegisterForm, LoginForm, ProfileForm, UserProfileForm

def register_view(request):
    if request.user.is_authenticated:
        return redirect('doctors:doctor_list')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                
                # Create the user profile if it doesn't exist
                UserProfile.objects.get_or_create(user=user)
                
                # Log the user in after registration
                login(request, user)
                messages.success(request, _('حساب کاربری شما با موفقیت ایجاد شد!'))
                return redirect('doctors:doctor_list')
    else:
        form = RegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'doctor'):
            return redirect('doctors:doctor_dashboard')
        return redirect('doctors:doctor_list')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me', False)
            
            # Try to find user by email
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                
                if user is not None:
                    login(request, user)
                    if not remember_me:
                        request.session.set_expiry(0)
                    messages.success(request, _('با موفقیت وارد شدید!'))
                    
                    # Redirect to appropriate dashboard/home based on user type
                    if hasattr(user, 'doctor'):
                        return redirect('doctors:doctor_dashboard')
                    return redirect('doctors:doctor_list')
                else:
                    messages.error(request, _('ایمیل یا رمز عبور نامعتبر است.'))
            except User.DoesNotExist:
                messages.error(request, _('ایمیل یا رمز عبور نامعتبر است.'))
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, _('با موفقیت خارج شدید.'))
    return redirect('doctors:doctor_list')

@login_required
def profile_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = ProfileForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('پروفایل شما با موفقیت به‌روزرسانی شد.'))
            return redirect('accounts:profile')
    else:
        user_form = ProfileForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def change_password_view(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(current_password):
            messages.error(request, _('رمز عبور فعلی صحیح نیست.'))
            return redirect('accounts:change_password')
        
        if new_password != confirm_password:
            messages.error(request, _('تکرار رمز عبور جدید مطابقت ندارد.'))
            return redirect('accounts:change_password')
        
        request.user.set_password(new_password)
        request.user.save()
        messages.success(request, _('رمز عبور شما با موفقیت تغییر یافت. لطفا مجددا وارد شوید.'))
        return redirect('login')
    
    return render(request, 'accounts/change_password.html')