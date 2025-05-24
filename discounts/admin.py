from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    DiscountType, Discount, CouponCode, DiscountUsage, 
    AutomaticDiscount, DiscountReport
)


@admin.register(DiscountType)
class DiscountTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'is_active', 'created_at')
    list_filter = ('type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


class CouponCodeInline(admin.TabularInline):
    model = CouponCode
    extra = 1
    fields = ('code', 'is_active')


class DiscountUsageInline(admin.TabularInline):
    model = DiscountUsage
    extra = 0
    readonly_fields = ('user', 'reservation', 'original_amount', 'discount_amount', 'final_amount', 'used_at')
    can_delete = False


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'discount_type', 'get_discount_value', 'applicable_to', 
        'status', 'used_count', 'usage_limit', 'is_valid_now', 'created_at'
    )
    list_filter = (
        'status', 'applicable_to', 'discount_type', 'is_public', 
        'start_date', 'end_date', 'created_at'
    )
    search_fields = ('title', 'description')
    readonly_fields = ('used_count', 'created_at', 'updated_at')
    filter_horizontal = ('doctors', 'specializations', 'clinics')
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'description', 'discount_type', 'status', 'is_public')
        }),
        ('مقدار تخفیف', {
            'fields': ('percentage', 'fixed_amount'),
            'description': 'فقط یکی از فیلدهای درصد یا مبلغ ثابت را پر کنید'
        }),
        ('شرایط اعمال', {
            'fields': ('applicable_to', 'doctors', 'specializations', 'clinics')
        }),
        ('محدودیت‌ها', {
            'fields': ('min_amount', 'max_discount_amount')
        }),
        ('تاریخ‌های اعتبار', {
            'fields': ('start_date', 'end_date')
        }),
        ('محدودیت استفاده', {
            'fields': ('usage_limit', 'usage_limit_per_user', 'used_count')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [CouponCodeInline, DiscountUsageInline]
    
    def get_discount_value(self, obj):
        if obj.discount_type.type == 'percentage':
            return f"{obj.percentage}%"
        elif obj.discount_type.type == 'fixed_amount':
            return f"{obj.fixed_amount} تومان"
        return "-"
    get_discount_value.short_description = 'مقدار تخفیف'
    
    def is_valid_now(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ معتبر</span>')
        else:
            return format_html('<span style="color: red;">✗ نامعتبر</span>')
    is_valid_now.short_description = 'وضعیت اعتبار'
    
    def save_model(self, request, obj, form, change):
        if not change:  # اگر در حال ایجاد است
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['activate_discounts', 'deactivate_discounts', 'generate_report']
    
    def activate_discounts(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} تخفیف فعال شد.')
    activate_discounts.short_description = 'فعال کردن تخفیفات انتخاب شده'
    
    def deactivate_discounts(self, request, queryset):
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} تخفیف غیرفعال شد.')
    deactivate_discounts.short_description = 'غیرفعال کردن تخفیفات انتخاب شده'


@admin.register(CouponCode)
class CouponCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount', 'is_active', 'is_valid_now', 'created_at')
    list_filter = ('is_active', 'discount__status', 'created_at')
    search_fields = ('code', 'discount__title')
    raw_id_fields = ('discount',)
    
    def is_valid_now(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ معتبر</span>')
        else:
            return format_html('<span style="color: red;">✗ نامعتبر</span>')
    is_valid_now.short_description = 'وضعیت اعتبار'


@admin.register(DiscountUsage)
class DiscountUsageAdmin(admin.ModelAdmin):
    list_display = (
        'get_user_name', 'discount', 'get_reservation_info', 
        'original_amount', 'discount_amount', 'final_amount', 'used_at'
    )
    list_filter = ('discount', 'used_at')
    search_fields = ('user__first_name', 'user__last_name', 'discount__title')
    readonly_fields = ('used_at',)
    raw_id_fields = ('discount', 'user', 'reservation', 'coupon_code')
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.phone
    get_user_name.short_description = 'کاربر'
    
    def get_reservation_info(self, obj):
        if obj.reservation:
            return f"{obj.reservation.doctor} - {obj.reservation.day.date}"
        return "-"
    get_reservation_info.short_description = 'اطلاعات رزرو'


@admin.register(AutomaticDiscount)
class AutomaticDiscountAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'discount', 'is_first_appointment', 'min_appointments_count', 
        'is_weekend', 'is_active', 'created_at'
    )
    list_filter = ('is_active', 'is_first_appointment', 'is_weekend', 'created_at')
    search_fields = ('name', 'discount__title')
    raw_id_fields = ('discount',)
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'discount', 'is_active')
        }),
        ('شرایط خودکار', {
            'fields': (
                'is_first_appointment', 'min_appointments_count', 
                'is_weekend', 'specific_days'
            ),
            'description': 'شرایطی که باید برای اعمال خودکار تخفیف برقرار باشد'
        })
    )


@admin.register(DiscountReport)
class DiscountReportAdmin(admin.ModelAdmin):
    list_display = (
        'discount', 'period_start', 'period_end', 'total_usage_count', 
        'total_discount_amount', 'total_revenue_impact', 'generated_at'
    )
    list_filter = ('period_start', 'period_end', 'generated_at')
    search_fields = ('discount__title',)
    readonly_fields = ('generated_at',)
    raw_id_fields = ('discount',)
    
    def has_add_permission(self, request):
        # گزارش‌ها معمولاً به صورت خودکار تولید می‌شوند
        return False


# تنظیمات اضافی برای نمایش بهتر
admin.site.site_header = 'مدیریت سیستم تخفیف دکتر ترن'
admin.site.site_title = 'مدیریت تخفیفات'
admin.site.index_title = 'پنل مدیریت تخفیفات' 