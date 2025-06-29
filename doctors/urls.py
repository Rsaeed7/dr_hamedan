from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('', views.index, name='index'),
    path('doctor_list', views.DoctorListView.as_view(), name='doctor_list'),
    path('specializations', views.specializations, name='specializations'),
    path('<int:pk>/', views.doctor_detail, name='doctor_detail'),
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('availability/', views.doctor_availability, name='doctor_availability'),
    path('earnings/', views.doctor_earnings, name='doctor_earnings'),
    path('appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('doctor/profile/', views.doctor_profile, name='doctor_profile'),
    path('appointment/<int:pk>/confirm/', views.confirm_appointment, name='confirm_appointment'),
    path('appointment/<int:pk>/complete/', views.complete_appointment, name='complete_appointment'),
    path('appointment/<int:pk>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('add-availability-day/', views.add_availability_day, name='add_availability_day'),
    path('edit-availability-day/<int:pk>/', views.edit_availability_day, name='edit_availability_day'),
    path('delete-availability-day/<int:pk>/', views.delete_availability_day, name='delete_availability_day'),
    path('update-settings/', views.update_settings, name='update_settings'),
    path('update-payment-settings/', views.update_payment_settings, name='update_payment_settings'),
    path('medexplor/', views.explore, name='medexplor'),
    path('register/', views.doctor_registration, name='doctor_registration'),

    path('inbox/', views.InboxView.as_view(), name='inbox'),
    path('doctor-search/', views.doctor_search, name='doctor-search'),
    path('sent/', views.SentMessagesView.as_view(), name='sent'),
    path('send/', views.SendMessageView.as_view(), name='send'),
    path('view/<uuid:pk>/', views.MessageDetailView.as_view(), name='detail'),
    path('reply/<uuid:pk>/', views.ReplyMessageView.as_view(), name='reply'),
    path('delete/<uuid:pk>/', views.DeleteMessageView.as_view(), name='delete'),
    path('templates/', views.email_template_list, name='email_template_list'),
    path('templates/create/', views.create_email_template, name='create_email_template'),
    path('important/', views.ImportantMessagesView.as_view(), name='important'),
    path('update-location/', views.update_doctor_location, name='update_location'),
    path('test-fonts/', views.test_fonts, name='test_fonts'),
] 