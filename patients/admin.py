from django.contrib import admin
from .models import PatientsFile,DrReportSettings,MedicalReport,ReportImage,ReportTemplate

admin.site.register(DrReportSettings)
admin.site.register(MedicalReport)
admin.site.register(ReportImage)
admin.site.register(ReportTemplate)

@admin.register(PatientsFile)
class PatientsFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'phone', 'birthdate', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'phone', 'national_id', 'user__username', 'user__email')
    date_hierarchy = 'created_at'
