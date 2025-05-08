from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('لاگین', views.LoginView.as_view(), name='login'),
    path('login/', views.RegisterView.as_view(), name='register'),
    path('logout', views.LogoutView.as_view(), name='logout'),
    path('check_code_login', views.CheckCodeView_Login.as_view(), name='check_code_login'),
    path('check_code_signup', views.CheckCodeView_Signup.as_view(), name='check_code_signup'),
    # path('add/address', views.AddAddressView.as_view(), name='add_address'),
    path('address_list', views.address_view, name='address_list'),
    path('address/<int:id>/delete/', views.delete_address, name='delete_address'),
    # path('user_coments', views.comments_view, name='comment_list'),
    path('profile', views.ProfileView.as_view(), name='profile'),
    # path('wishlist', views.wishlist_view, name='wishlist'),
    path('information', views.Informaiton, name='information'),
    # path('wishlist/<int:id>/delete/', views.wishlist_delete, name='delete_wish'),

]