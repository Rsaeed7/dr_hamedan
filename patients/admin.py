from django.contrib import admin
from .models import PatientsFile

@admin.register(PatientsFile)
class PatientsFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'phone', 'birthdate', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'phone', 'national_id', 'user__username', 'user__email')
    date_hierarchy = 'created_at'
