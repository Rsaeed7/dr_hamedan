from django.urls import path ,re_path
from . import views
app_name = 'mag'
urlpatterns = [
    path('',views.MagView.as_view(),name='list'),
    re_path('(?P<slug>[-\w]+)/',views.article, name='article'),
    # path('comments/<int:id>/delete/', views.comments_delete, name='delete_comment'),
]