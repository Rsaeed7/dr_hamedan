from wsgiref.validate import validator
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, redirect ,get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from patients.models import PatientsFile
from .forms import LoginForm, RegisterForm, Check_CodeForm
from django.contrib.auth import authenticate, login ,logout
from django.contrib import messages
from random import randint
from .models import Otp, User
from django.utils.crypto import get_random_string
from uuid import uuid4
import time
from datetime import datetime, timedelta
from utils.sms_service import sms_service

import time
from django.shortcuts import render
from .models import Otp
from .tasks import delete_expired_otp
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('doctors:index')
        else:
            form = RegisterForm()
            return render(request, 'registration/login.html', {'form': form})


    def post(self, request):
        form = RegisterForm(request.POST)

        if form.is_valid():
            cd = form.cleaned_data
            phone = cd["phone"]
            
            # Send verification code using centralized SMS service
            message, status_code, otp_code = sms_service.send_verification_code(phone)
            
            if status_code != 200:
                messages.error(request, message)
                return render(request, 'registration/login.html', {'form': form})
            
            # Create OTP record
            token = str(uuid4())
            Otp.objects.create(phone=phone, code=otp_code, token=token)
            
            # Store next URL if provided
            next_url = request.GET.get('next')
            if next_url:
                request.session['next_after_login'] = next_url
            
            # Redirect based on whether user exists
            if User.objects.filter(phone=phone).exists():
                messages.success(request, message)
                return redirect(reverse('account:check_code_login') + f'?token={token}')
            else:
                messages.success(request, message)
                return redirect(reverse('account:check_code_signup') + f'?token={token}')

        else:
            form.add_error('', '• لطفا اطلاعات صحیح وارد کنید!')

        return render(request, 'registration/login.html', {'form': form})

class CheckCodeView_Login(View):
    def get(self, request):
        form = Check_CodeForm()
        token = request.GET.get('token')
        phone = Otp.objects.get(token=token)
        return render(request, 'registration/check_login_code.html', {'form': form , 'phone':phone})

    def post(self, request):
        form = Check_CodeForm(request.POST)
        token = request.GET.get('token')
        phone = Otp.objects.get(token=token)
        if form.is_valid():
            cd = form.cleaned_data
            otp = Otp.objects.get(token=token)

            if otp.is_expired():
                messages.error(request, 'کد منقضی شده است')
                otp.delete()
                return redirect('account:check_code_login')

            if Otp.objects.filter(code=cd['code'], token=token).exists():
                user = User.objects.get(phone=otp.phone)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'شما با موفقیت وارد حساب کاربری خود شدید')
                otp.delete()
                next_url = request.session.pop('next_after_login', None)
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect('doctors:index')
            else:
                messages.error(request, 'کد تایید صحیح نیست')
        else:
            form.add_error('', '• لطفا اطلاعات صحیح وارد کنید!')

        return render(request, 'registration/check_login_code.html', {'form': form , 'phone':phone})

class CheckCodeView_Signup(View):
    def get(self, request):
        form = Check_CodeForm()
        token = request.GET.get('token')
        phone = Otp.objects.get(token=token)
        return render(request, 'registration/check_signup_code.html', {'form': form , 'phone':phone})

    def post(self, request):
        form = Check_CodeForm(request.POST)
        token = request.GET.get('token')
        phone = Otp.objects.get(token=token)
        if form.is_valid():
            cd = form.cleaned_data
            otp = Otp.objects.get(token=token)

            if otp.is_expired():
                messages.error(request, 'کد وارد شده منقضی شده است')
                otp.delete()
                return redirect('account:check_code_signup')

            if Otp.objects.filter(code=cd['code'], token=token).exists():
                user = User.objects.create(phone=otp.phone)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'عضویت  و ورود موفقیت آمیز')
                otp.delete()
                patient, created = PatientsFile.objects.get_or_create(
                    user=user,
                    defaults={
                        'phone': user.phone,
                    }
                )
                next_url = request.session.pop('next_after_login', None)
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect('doctors:index')
            else:
                messages.error(request, 'کد تایید صحیح نیست')
        else:
            form.add_error('', '• لطفا اطلاعات صحیح وارد کنید!')

        return render(request, 'registration/check_signup_code.html', {'form': form, 'phone':phone})

class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request,'شما با موفقیت از حساب کاربری خارج شدید')
        return redirect('doctors:index')
