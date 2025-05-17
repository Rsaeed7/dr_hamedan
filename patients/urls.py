from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('profile/', views.patient_profile, name='patient_profile'),
    path('appointments/', views.patient_appointments, name='patient_appointments'),
    path('dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('comments/', views.comments_view, name='comments'),
    path('comment/delete/<str:model_type>/<int:id>/', views.comment_delete, name='comments_delete'),
    path('record/<int:pk>/', views.MedicalRecordDetailView.as_view(), name='record-detail'),
    path('record/create/<int:patient_id>/', views.CreateMedicalRecordView.as_view(), name='create-record'),
    path('record/<int:record_id>/add-visit/', views.VisitEntryCreateView.as_view(), name='add-visit'),
    path('reports/', views.ReportListView.as_view(), name='report_list'),
    path('report/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('report/edit/<int:report_pk>/', views.edit_report, name='edit_report'),
    path('report/create/<int:patient_id>/', views.CreateReportView.as_view(), name='create_report'),
    path('report/settings', views.edit_report_settings, name='report_settings'),

]