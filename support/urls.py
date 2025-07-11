from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    path('about_us/', views.about_us, name='about_us'),
    path('for_doctors/', views.for_doctors, name='for_doctors'),
    path('frequently/', views.frequently, name='frequently'),
    path('contact_us/', views.contact_us, name='contact_us'),
    path('page_not_found/', views.page_not_found, name='404'),
    path('room/<int:room_id>/', views.chat_room, name='chat_room'),
    path('room/<int:room_id>/send_message/', views.send_message, name='send_message'),
    path('chat_room_list/', views.chat_room_list, name='chat_room_list'),
    path('create_auto/', views.create_auto_chat_room, name='create_auto_chat_room'),
    path('api/chat/messages/', views.get_chat_messages, name='chat_messages'),
]

