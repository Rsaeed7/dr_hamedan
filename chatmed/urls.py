from django.urls import path
from . import views
app_name = 'chat'


urlpatterns = [
    # درخواست‌های چت
    path('request/<int:doctor_id>/', views.request_chat, name='request_chat'),
    path('request-status/<int:request_id>/', views.request_status, name='request_status'),
    path('requests/<int:request_id>/<str:action>/', views.manage_chat_request, name='manage_request'),

    # اتاق‌های چت
    path('room/<int:room_id>/', views.chat_room, name='chat_room'),
    path('room/<int:room_id>/send/', views.send_message, name='send_message'),

    # لیست چت‌ها
    path('my-visits/', views.chat_room_list, name='chat_room_list'),

    # مدیریت وضعیت پزشک
    path('toggle-availability/', views.toggle_availability, name='toggle_availability'),

    # مدیریت درخواست ها
    path('', views.manage_chat, name='chat_home'),

    path('online_doctors/', views.OnDoctorListView.as_view(), name='list_doctors'),

    path('room/<int:room_id>/close/', views.close_chat, name='close_chat'),

    path('api/upload-file/', views.upload_file, name='upload_file'),
]
