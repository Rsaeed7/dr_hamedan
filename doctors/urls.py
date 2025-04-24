from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('', views.doctor_list, name='doctor_list'),
    path('<int:pk>/', views.doctor_detail, name='doctor_detail'),
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('availability/', views.doctor_availability, name='doctor_availability'),
    path('earnings/', views.doctor_earnings, name='doctor_earnings'),
    path('appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('profile/', views.doctor_profile, name='doctor_profile'),
    path('appointment/<int:pk>/confirm/', views.confirm_appointment, name='confirm_appointment'),
    path('appointment/<int:pk>/complete/', views.complete_appointment, name='complete_appointment'),
    path('appointment/<int:pk>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('add-availability-day/', views.add_availability_day, name='add_availability_day'),
    path('edit-availability-day/<int:pk>/', views.edit_availability_day, name='edit_availability_day'),
    path('delete-availability-day/<int:pk>/', views.delete_availability_day, name='delete_availability_day'),
    path('update-settings/', views.update_settings, name='update_settings'),
    path('update-payment-settings/', views.update_payment_settings, name='update_payment_settings'),
] 