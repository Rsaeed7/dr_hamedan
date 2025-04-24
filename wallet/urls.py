from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    path('', views.wallet_dashboard, name='wallet_dashboard'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('payment/<int:reservation_id>/', views.process_payment, name='process_payment'),
    path('payment-callback/', views.payment_callback, name='payment_callback'),
] 