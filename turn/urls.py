from django.urls import path
from . import views
app_name = 'turn'
urlpatterns = [
    path('', views.turn, name='turn_days'),
    path('make/', views.turn_maker, name='turn_maker'),
    path('تایید/', views.confirm, name='confirm')
]

