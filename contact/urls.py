from django.urls import path
from . import views

app_name = 'contact'

urlpatterns = [
    path('about_us/', views.about_us, name='about'),
    path('contact_us/', views.contact_us, name='contact_us'),
]