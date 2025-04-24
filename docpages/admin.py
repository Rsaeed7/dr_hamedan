from django.contrib import admin
from .models import Post, Comment

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'doctor', 'created_at', 'likes')
    list_filter = ('doctor', 'created_at')
    search_fields = ('title', 'content', 'doctor__user__first_name', 'doctor__user__last_name')
    date_hierarchy = 'created_at'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'post', 'created_at', 'approved')
    list_filter = ('approved', 'created_at')
    search_fields = ('name', 'email', 'body')
    actions = ['approve_comments']
    
    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
    approve_comments.short_description = "Approve selected comments"
