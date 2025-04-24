from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _

from .models import User
from .forms import RegisterForm, LoginForm, ProfileForm

def register_view(request):
    if request.user.is_authenticated:
        return redirect('doctors:doctor_list')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            user.set_password(password)
            user.save()
            
            # Log the user in after registration
            login(request, user)
            messages.success(request, _('Account created successfully!'))
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
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, _('Logged in successfully!'))
                
                # Redirect to appropriate dashboard/home based on user type
                if hasattr(user, 'doctor'):
                    return redirect('doctors:doctor_dashboard')
                return redirect('doctors:doctor_list')
            else:
                messages.error(request, _('Invalid email or password.'))
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, _('Logged out successfully.'))
    return redirect('doctors:doctor_list')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Profile updated successfully.'))
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form}) 