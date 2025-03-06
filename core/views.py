from django.shortcuts import render

def home(request):
    return render(request, 'core/homepage.html')

def special_list(request):
    return render(request, 'doctor/specialties_list.html')

def special_dr_list(request):
    return render(request, 'doctor/expertise_list.html')

def clinic_list(request):
    return render(request, 'clinic/clinic_list.html')

def clinic_detail(request):
    return render(request, 'clinic/clinic_detail.html')


def dr_detail(request):
        return render(request, 'doctor/dr_detail.html')


def article_list(request):
    return render(request, 'blog/article_list.html')

def article_detail(request):
    return render(request, 'blog/article_detail.html')
# Create your views here.

def login(request):
    return render(request, 'account/login.html')

def check_code(request):
    return render(request, 'account/check_code.html')

def profile(request):
    return render(request, 'account/profile.html')