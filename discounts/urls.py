from django.urls import path
from . import views

app_name = 'discounts'

urlpatterns = [
    # صفحات عمومی
    path('', views.DiscountListView.as_view(), name='discount_list'),
    path('<int:pk>/', views.DiscountDetailView.as_view(), name='discount_detail'),
    
    # تاریخچه کاربر
    path('history/', views.user_discount_history, name='user_discount_history'),
    
    # API endpoints
    path('api/apply-coupon/', views.apply_coupon_code, name='apply_coupon_code'),
    path('api/check-automatic/', views.check_automatic_discounts, name='check_automatic_discounts'),
    path('api/available/', views.get_available_discounts, name='get_available_discounts'),
    path('api/remove/', views.remove_discount, name='remove_discount'),
    path('api/validate-coupon/', views.validate_coupon_code, name='validate_coupon_code'),
] 