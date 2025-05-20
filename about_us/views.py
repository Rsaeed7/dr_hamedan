from django.shortcuts import render,redirect
from .forms import ContactForm
from django.contrib import messages


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
