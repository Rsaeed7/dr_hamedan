from django.urls import path
from . import views

app_name = 'clinics'

urlpatterns = [
    path('', views.ClinicListView.as_view(), name='clinic_list'),
    path('dashboard/', views.clinic_dashboard, name='clinic_dashboard'),
    path('profile/', views.clinic_profile, name='clinic_profile'),
    path('doctors/', views.clinic_doctors, name='clinic_doctors'),
    path('appointments/', views.clinic_appointments, name='clinic_appointments'),
    path('gallery/delete/<int:pk>/', views.delete_gallery_image, name='delete_gallery_image'),
    path('<slug:slug>/', views.clinic_detail, name='clinic_detail'),
]