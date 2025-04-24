from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    path('book/<int:doctor_id>/', views.book_appointment, name='book_appointment'),
    path('confirm/<int:pk>/', views.confirm_appointment, name='confirm_appointment'),
    path('cancel/<int:pk>/', views.cancel_appointment, name='cancel_appointment'),
    path('complete/<int:pk>/', views.complete_appointment, name='complete_appointment'),
    path('status/<int:pk>/', views.appointment_status, name='appointment_status'),
    path('view/<int:pk>/', views.view_appointment, name='view_appointment'),
    path('manage-days/', views.manage_reservation_days, name='manage_reservation_days'),
] 