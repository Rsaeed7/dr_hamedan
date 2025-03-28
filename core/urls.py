from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomePageView.as_view(), name='homepage'),
    path('clinics', views.clinic_list, name='clinic_list'),
    path('special_list', views.special_list, name='special_list'),
    path('special_list_dr', views.special_dr_list, name='special_list_dr'),
    path('clinic_detail', views.clinic_detail, name='clinic_detail'),
    path('dr_detail', views.dr_detail, name='dr_detail'),
    path('login', views.login, name='login'),
    path('check_code', views.check_code, name='check_code'),
    path('profile', views.profile, name='profile'),
]