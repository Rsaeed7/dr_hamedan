from django.urls import path
from . import views

app_name = 'clinics'

urlpatterns = [
    path('', views.clinic_list, name='clinic_list'),
    path('<int:clinic_id>/', views.clinic_detail, name='clinic_detail'),
    path('dashboard/', views.clinic_dashboard, name='dashboard'),
] 