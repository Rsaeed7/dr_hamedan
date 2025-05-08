from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('profile/', views.patient_profile, name='patient_profile'),
    path('appointments/', views.patient_appointments, name='patient_appointments'),
    path('dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('comments/', views.comments_view, name='comments'),
    path('comment/delete/<str:model_type>/<int:id>/', views.comment_delete, name='comments_delete'),

]