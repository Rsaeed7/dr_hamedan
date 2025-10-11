from django.urls import path
from . import views

app_name = 'doctors'


urlpatterns = [
    path('', views.index, name='index'),
    path('registration/', views.doctor_registration, name='doctor_registration'),
    path('list/', views.DoctorListView.as_view(), name='doctor_list'),
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('availability/', views.doctor_availability, name='doctor_availability'),
    path('earnings/', views.doctor_earnings, name='doctor_earnings'),
    path('appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('appointments_today/', views.doctor_appointments_today, name='doctor_appointments_today'),
    path('appointments-tabs/', views.doctor_appointments_tabs, name='doctor_appointments_tabs'),
    path('profile/', views.doctor_profile, name='doctor_profile'),
    path('confirm-appointment/<int:pk>/', views.confirm_appointment, name='confirm_appointment'),
    path('complete-appointment/<int:pk>/', views.complete_appointment, name='complete_appointment'),
    path('cancel-appointment/<int:pk>/', views.cancel_appointment, name='cancel_appointment'),
    path('toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('add-availability/', views.add_availability_day, name='add_availability_day'),
    path('update-settings/', views.update_settings, name='update_settings'),
    path('delete-availability/<int:pk>/', views.delete_availability_day, name='delete_availability_day'),
    path('edit-availability/<int:pk>/', views.edit_availability_day, name='edit_availability_day'),
    path('update-payment/', views.update_payment_settings, name='update_payment_settings'),
    path('explore/', views.explore, name='explore'),
    path('specializations/', views.specializations, name='specializations'),
    
    # Blocked Days Management
    path('blocked-days/', views.manage_blocked_days, name='manage_blocked_days'),
    path('add-blocked-day/', views.add_blocked_day, name='add_blocked_day'),
    path('remove-blocked-day/<int:pk>/', views.remove_blocked_day, name='remove_blocked_day'),
    path('api/blocked-days/', views.get_blocked_days_json, name='get_blocked_days_json'),
    
    # Email/Messaging URLs
    path('inbox/', views.InboxView.as_view(), name='inbox'),
    path('sent/', views.SentMessagesView.as_view(), name='sent_messages'),
    path('important/', views.ImportantMessagesView.as_view(), name='important_messages'),
    path('message/<uuid:pk>/', views.MessageDetailView.as_view(), name='message_detail'),
    path('send/', views.SendMessageView.as_view(), name='send_message'),
    path('reply/<uuid:pk>/', views.ReplyMessageView.as_view(), name='reply_message'),
    path('delete-message/<uuid:pk>/', views.DeleteMessageView.as_view(), name='delete_message'),
    path('email-templates/', views.email_template_list, name='email_template_list'),
    path('create-email-template/', views.create_email_template, name='create_email_template'),
    
    # Location update
    path('update-location/', views.update_doctor_location, name='update_doctor_location'),
    
    # Doctor search API
    path('api/search/', views.doctor_search, name='doctor_search'),
    
    # Test fonts
    path('test-fonts/', views.test_fonts, name='test_fonts'),
    
    # Notification URLs
    path('notifications/', views.notifications_page, name='notifications'),
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('api/notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('api/notifications/test/', views.create_test_notification, name='create_test_notification'),
    path('doctor/<slug:slug>/', views.doctor_detail, name='doctor_detail'),
] 