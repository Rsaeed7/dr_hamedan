from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Dashboard and main views
    path('', views.payment_dashboard, name='payment_dashboard'),
    path('list/', views.payment_list, name='payment_list'),
    path('detail/<int:payment_id>/', views.payment_detail, name='payment_detail'),
    
    # Payment creation
    path('create/', views.create_payment, name='create_payment'),
    path('wallet-deposit/', views.wallet_deposit_payment, name='wallet_deposit'),
    path('reservation/<int:reservation_id>/', views.reservation_payment, name='reservation_payment'),
    path('chat/<int:chat_request_id>/', views.chat_payment, name='chat_payment'),
    
    # Payment callback
    path('callback/', views.payment_callback, name='payment_callback'),
    
    # API endpoints
    path('api/status/<int:payment_id>/', views.api_payment_status, name='api_payment_status'),
    path('api/create/', views.api_create_payment, name='api_create_payment'),
    path('api/verify/', views.api_verify_payment, name='api_verify_payment'),
] 