from django.urls import path
from . import views

app_name = 'docpages'

urlpatterns = [
    path('doctor/<int:doctor_id>/', views.doctor_page, name='doctor_page'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('my-posts/', views.doctor_posts, name='doctor_posts'),
    path('create-post/', views.create_post, name='create_post'),
    path('edit-post/<int:post_id>/', views.edit_post, name='edit_post'),
    path('delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('manage-comments/', views.manage_comments, name='manage_comments'),
    
    # AJAX endpoints
    path('ajax/toggle-like/<int:post_id>/', views.toggle_like, name='toggle_like'),
    path('ajax/search-medical-lenses/', views.search_medical_lenses, name='search_medical_lenses'),

] 