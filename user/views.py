from wsgiref.validate import validator
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, redirect ,get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from .forms import LoginForm, RegisterForm, Check_CodeForm, UserAddress
from django.contrib.auth import authenticate, login ,logout
from django.contrib import messages
# import ghasedakpack
from random import randint
from .models import Otp, User
from django.utils.crypto import get_random_string
from uuid import uuid4
import time
from datetime import datetime, timedelta
# sender = ghasedakpack.Ghasedak('2a2134a3503074b682413eb874c5df026b4ed60280b89465a1d3fe80766ce2cc')

import time
from django.shortcuts import render
from .models import Otp
from .tasks import delete_expired_otp
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required




class ProfileView(LoginRequiredMixin,TemplateView):
    template_name = 'registration/profile.html'


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('core:homepage')
        else:
            form = LoginForm()
            return render(request, 'registration/sign_in.html',{'form':form})
    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(username=cd['username'], password=cd['password'])
            if user is not None:
                login(request, user)
                messages.success(request, f'{user.name} خوش آمدی ')
                return redirect('core:homepage')
            else:
                form.add_error('username','• شماره موبایل یا رمز عبور نادرست است!')
        else:
            form.add_error('','• لطفا اطلاعات صحیح وارد کنید!')

        return render(request, 'registration/sign_in.html',{'form':form})



class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('core:homepage')
        else:
            form = RegisterForm()
            return render(request, 'registration/login.html', {'form': form})


    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            random = randint(1000,9999)
            # sender.verification({'receptor': cd["phone"], 'type': '1', 'template': 'Randomcode', 'param1': random})
            token = str(uuid4())
            if User.objects.filter(phone=cd['phone']):
                Otp.objects.create(phone=cd["phone"],code=random,token=token)
                print(random)
                return redirect(reverse('account:check_code_login') + f'?token={token}')
            else:
                Otp.objects.create(phone=cd["phone"],code=random,token=token)
                print(random)
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



# class AddAddressView(View):
#     def post(self, request):
#         if not request.user.is_authenticated:
#             return redirect('core:homepage')
#         else:
#             form = AddressForm(request.POST)
#             if form.is_valid():
#                 address = form.save(commit=False)
#                 address.user = request.user
#                 address.save()
#                 next_page = request.GET.get('next')
#                 if next_page:
#                     return redirect(next_page)
#                 else:
#                     return redirect('account:address_list')
#     def get(self, request):
#         if not request.user.is_authenticated:
#             return redirect('core:homepage')
#         else:
#             form = AddressForm()
#             return render(request, 'account/add_address.html' , {'form':form})

@login_required()
def address_view(request):
    return render(request, 'registration/address_list.html')
@login_required()
def delete_address(request,id):
    address = get_object_or_404(UserAddress,id=id)
    address.delete()
    time.sleep(3)
    return redirect('account:address_list')



# @login_required()
# def wishlist_view(request):
#     return render(request,'account/user-wishlist.html')
#
#
# @login_required()
# def wishlist_delete(request,id):
#     product_wish = get_object_or_404(UserWishList,id=id)
#     product_wish.delete()
#     time.sleep(2)
#     return redirect('account:wishlist')

@login_required()
def Informaiton(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        email_validator = EmailValidator()
        try:
            email_validator(email)
        except ValidationError:
            messages.error(request, "ایمیل وارد شده معتبر نیست")
            return redirect('account:information')
        # چک کردن تکراری بودن ایمیل
        if User.objects.filter(email=email).exclude(id=request.user.id).exists():
            messages.error(request, "ایمیل وارد شده تکراری است")
            return redirect('account:information')
        user = User.objects.filter(id=request.user.id)
        if not age:
            age = None
        if not email or name == '':
            return redirect('account:information')
        user.update(name=name, email=email, age=age, gender=gender)
        messages.success(request, "اطلاعات با موفقیت به روز شد")
        return redirect('account:information')

    return render(request, 'registration/account_Information.html')