from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum
from .models import Transaction, Wallet, PaymentGateway


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'pending_balance', 'frozen_balance', 'get_total_balance', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'get_total_balance']
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user',)
        }),
        ('موجودی', {
            'fields': ('balance', 'pending_balance', 'frozen_balance', 'get_total_balance')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_total_balance(self, obj):
        return obj.get_total_balance()
    get_total_balance.short_description = 'کل موجودی'
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'commission_percentage', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('name', 'code', 'is_active')
        }),
        ('تنظیمات API', {
            'fields': ('api_key', 'merchant_id', 'gateway_url', 'verify_url'),
            'classes': ('collapse',)
        }),
        ('محدودیت‌ها', {
            'fields': ('min_amount', 'max_amount')
        }),
        ('کمیسیون', {
            'fields': ('commission_percentage',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'tracking_code', 'user', 'transaction_type', 'amount', 'net_amount', 
        'status', 'payment_method', 'gateway', 'created_at'
    ]
    list_filter = [
        'transaction_type', 'status', 'payment_method', 'gateway', 
        'created_at', 'processed_at'
    ]
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'tracking_code', 'reference_id', 'authority', 'description'
    ]
    readonly_fields = [
        'tracking_code', 'created_at', 'updated_at', 'processed_at',
        'net_amount', 'commission_amount', 'get_related_reservations'
    ]
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('user', 'wallet', 'tracking_code', 'transaction_type', 'status')
        }),
        ('مبالغ', {
            'fields': ('amount', 'commission_amount', 'net_amount')
        }),
        ('پرداخت', {
            'fields': ('payment_method', 'gateway', 'authority', 'reference_id')
        }),
        ('توضیحات', {
            'fields': ('description', 'failure_reason')
        }),
        ('روابط', {
            'fields': ('related_transaction', 'get_related_reservations'),
            'classes': ('collapse',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at', 'processed_at'),
            'classes': ('collapse',)
        }),
        ('متادیتا', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_failed', 'mark_as_pending']
    
    def get_related_reservations(self, obj):
        reservations = obj.reservations.all()
        if reservations.exists():
            links = []
            for reservation in reservations:
                url = reverse('admin:reservations_reservation_change', args=[reservation.id])
                links.append(format_html('<a href="{}">{}</a>', url, str(reservation)))
            return format_html('<br>'.join(links))
        return 'ندارد'
    get_related_reservations.short_description = 'رزروهای مرتبط'
    
    def mark_as_completed(self, request, queryset):
        updated = 0
        for transaction in queryset:
            if transaction.status in ['pending', 'processing']:
                transaction.mark_as_completed()
                updated += 1
        
        self.message_user(request, f'{updated} تراکنش به عنوان تکمیل شده علامت‌گذاری شد.')
    mark_as_completed.short_description = 'علامت‌گذاری به عنوان تکمیل شده'
    
    def mark_as_failed(self, request, queryset):
        updated = 0
        for transaction in queryset:
            if transaction.status in ['pending', 'processing']:
                transaction.mark_as_failed('تغییر وضعیت توسط ادمین')
                updated += 1
        
        self.message_user(request, f'{updated} تراکنش به عنوان ناموفق علامت‌گذاری شد.')
    mark_as_failed.short_description = 'علامت‌گذاری به عنوان ناموفق'
    
    def mark_as_pending(self, request, queryset):
        updated = queryset.filter(status__in=['failed', 'cancelled']).update(
            status='pending',
            failure_reason='',
            processed_at=None
        )
        self.message_user(request, f'{updated} تراکنش به حالت در انتظار بازگردانده شد.')
    mark_as_pending.short_description = 'بازگردانی به حالت در انتظار'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'wallet', 'gateway', 'related_transaction'
        ).prefetch_related('reservations')


# تنظیمات اضافی برای نمایش بهتر
admin.site.site_header = 'مدیریت سیستم دکتر ترن'
admin.site.site_title = 'دکتر ترن'
admin.site.index_title = 'پنل مدیریت'
