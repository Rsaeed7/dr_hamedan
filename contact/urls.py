from django.urls import path
from . import views

app_name = 'contact'

urlpatterns = [
    # path('درباره_ما/', views.about_us, name='about'),
    path('تماس_باما/', views.contact_us, name='contact_us'),
]