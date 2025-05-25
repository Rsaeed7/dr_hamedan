from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    # Dashboard and main views
    path('', views.wallet_dashboard, name='wallet_dashboard'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transaction/<int:transaction_id>/', views.transaction_detail, name='transaction_detail'),
    
    # Deposit and withdraw
    path('deposit/', views.deposit, name='deposit'),
    path('withdraw/', views.withdraw, name='withdraw'),
    
    # Payment processing
    path('payment/<int:reservation_id>/', views.process_payment, name='process_payment'),
    path('payment-gateway/<int:transaction_id>/', views.payment_gateway, name='payment_gateway'),
    path('payment-callback/', views.payment_callback, name='payment_callback'),
    
    # Refund
    path('refund/<int:transaction_id>/', views.request_refund, name='request_refund'),
    
    # API endpoints
    path('api/balance/', views.wallet_api_balance, name='api_balance'),
] 