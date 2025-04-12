from django.urls import path
from . import views
app_name = 'turn'
urlpatterns = [
    path('', views.turn, name='turn_days'),
    path('make/', views.turn_maker, name='turn_maker'),
    path('تایید/', views.confirm, name='confirm'),
    path('payment/<int:reservation_id>/', views.payment_confirmation, name='payment_confirmation'),
    path('payment-redirect/<int:reservation_id>/', views.payment_redirect, name='payment_redirect'),
    path('doctor-slots/<int:doctor_id>/<int:date_id>/', views.get_doctor_slots, name='doctor_slots'),
]

