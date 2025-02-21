from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='homepage'),
    path('clinics', views.clinic_list, name='clinic_list'),
]