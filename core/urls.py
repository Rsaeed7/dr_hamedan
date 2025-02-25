from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='homepage'),
    path('clinics', views.clinic_list, name='clinic_list'),
    path('clinic_detail', views.clinic_detail, name='clinic_detail'),
    path('article_list', views.article_list, name='article_list'),
    path('article_detail', views.article_detail, name='article_detail'),
    path('dr_detail', views.dr_detail, name='dr_detail'),
]