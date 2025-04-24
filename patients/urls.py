from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('profile/', views.patient_profile, name='patient_profile'),
    path('appointments/', views.patient_appointments, name='patient_appointments'),
    path('dashboard/', views.patient_dashboard, name='patient_dashboard'),
] 