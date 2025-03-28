from django.shortcuts import render
from django.views.generic import TemplateView
from mag.models import MagArticle



class HomePageView(TemplateView):
    template_name = 'core/homepage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['articles'] = MagArticle.objects.filter(published=True).order_by("date")[:9]
        return context


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


def login(request):
    return render(request, 'account/login.html')

def check_code(request):
    return render(request, 'account/check_code.html')

def profile(request):
    return render(request, 'account/profile.html')