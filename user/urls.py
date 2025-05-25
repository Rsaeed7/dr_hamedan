from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('login/', views.RegisterView.as_view(), name='register'),
    path('logout', views.LogoutView.as_view(), name='logout'),
    path('check_code_login', views.CheckCodeView_Login.as_view(), name='check_code_login'),
    path('check_code_signup', views.CheckCodeView_Signup.as_view(), name='check_code_signup'),
]