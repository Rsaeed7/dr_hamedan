from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import PaymentGateway, PaymentRequest, PaymentLog


@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'gateway_type', 'is_active', 'is_sandbox', 
        'commission_percentage', 'created_at'
    ]
    list_filter = ['gateway_type', 'is_active', 'is_sandbox', 'created_at']
    search_fields = ['name', 'merchant_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('name', 'gateway_type', 'is_active', 'is_sandbox')
        }),
        ('تنظیمات API', {
            'fields': ('merchant_id', 'api_key', 'callback_url'),
            'classes': ('collapse',)
        }),
        ('آدرس‌های زرین‌پال', {
            'fields': ('zp_api_request', 'zp_api_verify', 'zp_api_startpay'),
            'classes': ('collapse',)
        }),
        ('محدودیت‌ها', {
            'fields': ('min_amount', 'max_amount')
        }),
        ('کمیسیون', {
            'fields': ('commission_percentage', 'fixed_commission')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'amount', 'gateway', 'status', 
        'authority', 'created_at', 'get_transaction_link'
    ]
    list_filter = [
        'status', 'gateway__gateway_type', 'created_at', 'completed_at'
    ]
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'authority', 'ref_id', 'description'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'completed_at', 'expires_at',
        'get_transaction_link', 'get_logs_link'
    ]
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('user', 'wallet', 'amount', 'description', 'status')
        }),
        ('درگاه پرداخت', {
            'fields': ('gateway', 'authority', 'ref_id', 'card_pan')
        }),
        ('اطلاعات اضافی', {
            'fields': ('callback_url', 'metadata'),
            'classes': ('collapse',)
        }),
        ('تراکنش مرتبط', {
            'fields': ('transaction', 'get_transaction_link'),
            'classes': ('collapse',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at', 'completed_at', 'expires_at'),
            'classes': ('collapse',)
        }),
        ('لاگ‌ها', {
            'fields': ('get_logs_link',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_failed', 'mark_as_pending']
    
    def get_transaction_link(self, obj):
        if obj.transaction:
            url = reverse('admin:wallet_transaction_change', args=[obj.transaction.id])
            return format_html('<a href="{}">{}</a>', url, str(obj.transaction))
        return 'ندارد'
    get_transaction_link.short_description = 'تراکنش مرتبط'
    
    def get_logs_link(self, obj):
        logs_count = obj.logs.count()
        if logs_count > 0:
            url = reverse('admin:payments_paymentlog_changelist') + f'?payment_request__id__exact={obj.id}'
            return format_html('<a href="{}">{} لاگ</a>', url, logs_count)
        return 'ندارد'
    get_logs_link.short_description = 'لاگ‌ها'
    
    def mark_as_completed(self, request, queryset):
        updated = 0
        for payment_request in queryset:
            if payment_request.can_be_processed():
                payment_request.mark_as_completed()
                updated += 1
        
        self.message_user(request, f'{updated} درخواست پرداخت به عنوان تکمیل شده علامت‌گذاری شد.')
    mark_as_completed.short_description = 'علامت‌گذاری به عنوان تکمیل شده'
    
    def mark_as_failed(self, request, queryset):
        updated = 0
        for payment_request in queryset:
            if payment_request.can_be_processed():
                payment_request.mark_as_failed('تغییر وضعیت توسط ادمین')
                updated += 1
        
        self.message_user(request, f'{updated} درخواست پرداخت به عنوان ناموفق علامت‌گذاری شد.')
    mark_as_failed.short_description = 'علامت‌گذاری به عنوان ناموفق'
    
    def mark_as_pending(self, request, queryset):
        updated = queryset.filter(status__in=['failed', 'cancelled', 'expired']).update(
            status='pending',
            completed_at=None
        )
        self.message_user(request, f'{updated} درخواست پرداخت به حالت در انتظار بازگردانده شد.')
    mark_as_pending.short_description = 'بازگردانی به حالت در انتظار'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'wallet', 'gateway', 'transaction'
        )


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = [
        'payment_request', 'log_type', 'message', 'created_at'
    ]
    list_filter = ['log_type', 'created_at']
    search_fields = [
        'payment_request__user__username',
        'payment_request__authority',
        'message'
    ]
    readonly_fields = ['created_at', 'get_payment_request_link']
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('payment_request', 'get_payment_request_link', 'log_type', 'message')
        }),
        ('داده‌ها', {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_payment_request_link(self, obj):
        url = reverse('admin:payments_paymentrequest_change', args=[obj.payment_request.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.payment_request))
    get_payment_request_link.short_description = 'درخواست پرداخت'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# تنظیمات اضافی برای نمایش بهتر
admin.site.site_header = 'مدیریت سیستم دکتر ترن'
admin.site.site_title = 'دکتر ترن'
admin.site.index_title = 'پنل مدیریت' 