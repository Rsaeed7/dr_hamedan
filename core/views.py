from django.shortcuts import render

def home(request):
    return render(request, 'core/homepage.html')


def clinic_list(request):
    return render(request, 'clinic/clinic_list.html')

def clinic_detail(request):
    return render(request, 'clinic/clinic_detail.html')


def article_list(request):
    return render(request, 'blog/article_list.html')
# Create your views here.
