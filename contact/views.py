from django.shortcuts import render,redirect
from .forms import ContactForm
from django.contrib import messages

def about_us(request):
    return render(request, 'contact/about_us.html')



def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,'پیام شما با موفقیت برای ما ارسال شد! ممنونیم که وقت گذاشتید:)')
            return redirect('contact:contact_us')
    else:
        form = ContactForm()
    return render(request,'contact/contact_us.html',{'form':form})
# Create your views here.
