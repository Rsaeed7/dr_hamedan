from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_type', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('user__username', 'user__email', 'description')
    date_hierarchy = 'created_at'
    
    actions = ['mark_as_completed', 'mark_as_failed']
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, "Selected transactions have been marked as completed.")
    mark_as_completed.short_description = "Mark selected transactions as completed"
    
    def mark_as_failed(self, request, queryset):
        queryset.update(status='failed')
        self.message_user(request, "Selected transactions have been marked as failed.")
    mark_as_failed.short_description = "Mark selected transactions as failed"
