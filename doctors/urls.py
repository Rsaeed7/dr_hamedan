from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('', views.doctor_list, name='doctor_list'),
    path('<int:doctor_id>/', views.doctor_detail, name='doctor_detail'),
    path('dashboard/', views.doctor_dashboard, name='dashboard'),
    path('analytics/', views.doctor_analytics, name='analytics'),
    path('appointment/<int:appointment_id>/update-status/', views.update_appointment_status, name='update_appointment_status'),
] 