from django.urls import path
from . import views
app_name = 'chat'


urlpatterns = [
    # درخواست‌های چت
    path('request/<int:doctor_id>/', views.request_chat, name='request_chat'),
    path('requests/<int:request_id>/<str:action>/', views.manage_chat_request, name='manage_request'),

    # اتاق‌های چت
    path('room/<int:room_id>/', views.chat_room, name='chat_room'),
    path('room/<int:room_id>/send/', views.send_message, name='send_message'),

    # لیست چت‌ها
    path('my-visits/', views.chat_room_list, name='chat_room_list'),

    # مدیریت وضعیت پزشک
    path('toggle-availability/', views.toggle_availability, name='toggle_availability'),

    # صفحه اصلی
    path('', views.home, name='chat_home'),

    path('doctors/', views.list_doctors, name='list_doctors'),
]
