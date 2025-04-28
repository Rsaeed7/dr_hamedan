from django.urls import path
from . import views

app_name = 'about'

urlpatterns = [
    path('about_us/', views.about_us, name='about_us'),
    path('contact_us/', views.contact_us, name='contact_us'),
    path('page_not_found/', views.page_not_found, name='404')
]