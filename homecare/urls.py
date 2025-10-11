from django.urls import path
from . import views

app_name = 'homecare'

urlpatterns = [
    path('services/', views.select_service_view, name='select_service'),
    path('services/request/<slug:service_slug>/', views.request_service, name='request_service'),
    path('success/', views.request_success, name='success'),
    path('requests/cancel/<int:request_id>/', views.cancel_homecare_request, name='cancel_homecare'),
    path('admin/', views.admin_homecare_requests, name='admin_requests_list'),
    path('admin/requests/<int:request_id>/', views.admin_request_detail, name='admin_request_detail'),
]
