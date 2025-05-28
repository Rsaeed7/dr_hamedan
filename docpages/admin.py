from django.contrib import admin
from .models import Post, Comment, MedicalLens, PostLike


@admin.register(MedicalLens)
class MedicalLensAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'color', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'name': ('name',)}
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'color')
        }),
    )


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('post__title', 'user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'doctor', 'media_type', 'status', 'get_like_count', 'created_at')
    list_filter = ('doctor', 'status', 'media_type', 'medical_lenses', 'created_at')
    search_fields = ('title', 'content', 'doctor__user__first_name', 'doctor__user__last_name')
    date_hierarchy = 'created_at'
    filter_horizontal = ('medical_lenses',)
    readonly_fields = ('media_type', 'likes_count', 'get_like_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('doctor', 'title', 'content', 'status')
        }),
        ('رسانه', {
            'fields': ('media_type', 'image', 'video'),
            'description': 'فقط یک نوع رسانه (تصویر یا ویدیو) انتخاب کنید.'
        }),
        ('برچسب‌ها', {
            'fields': ('medical_lenses',)
        }),
        ('آمار', {
            'fields': ('likes_count', 'get_like_count'),
            'classes': ('collapse',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_like_count(self, obj):
        return obj.get_like_count()
    get_like_count.short_description = 'تعداد واقعی لایک‌ها'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'post', 'created_at', 'approved')
    list_filter = ('approved', 'created_at')
    search_fields = ('name', 'email', 'body', 'post__title')
    actions = ['approve_comments']
    
    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
    approve_comments.short_description = 'تایید نظرات انتخاب شده'
