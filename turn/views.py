from django.shortcuts import render,HttpResponse,redirect
from jdatetime import date ,timedelta
from turn.utils.turn_maker import create_reservations
from .models import Reservation_Day,Reservation,Patients_File
from .forms import ReservationForm
import re
from django.contrib import messages



def turn(request):
    today = date.today()
    cutoff_date = today + timedelta(days=90)
    reservations_Day = Reservation_Day.objects.filter(published=True, date__lte=cutoff_date)
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            id = request.POST.get('id')
            name = re.sub(' +', ' ',cd['name'])
            reservation = Reservation.objects.filter(id=id)
            message = f"{cd['name']} عزیز نوبت شما در  تاریخ ({reservation[0].day}) و ساعت ({reservation[0].time}) ثبت شد. لطفا راس ساعت در مطب حضور داشته باشید."
            if Patients_File.objects.filter(name=name,meli_code=cd['meli_code']):
                user = Patients_File.objects.get(name=name,meli_code=cd['meli_code'])
                reservation.update(patient=user,phone=cd['phone'])
                messages.success(request, message)
                return redirect('turn:confirm')
            else:
                user = Patients_File.objects.create(name=name,phone=cd['phone'],meli_code=cd['meli_code'])
                reservation.update(patient=user)
                messages.success(request, message)
                return redirect('turn:confirm')
        else:
            messages.error(request,"لطفا شماره تلفن و کد ملی صحیح وارد کنید")
            return redirect('turn:turn_days')
    else:
        form = ReservationForm()
    return render(request, 'turn/turn.html', {'reservations_Day':reservations_Day,'form':form, 'today':today})


def turn_maker(request):
    if request.user.is_authenticated:
        create_reservations()
        return HttpResponse('نوبت ها تا یک سال آینده ساخته شدند لطفا روزهای تعطیل رسمی و تعطیلی های مطب را به حالت نوبت غیر فعال تغییر دهید')
    else:
        return HttpResponse('ابتدا وارد حساب کاربری خود شوید')


def confirm(request):
    return render(request, 'turn/confirm.html')
