from django.shortcuts import render

def home(request):
    return render(request, 'core/homepage.html')


def clinic_list(request):
    return render(request, 'clinic/clinic_list.html')
# Create your views here.
