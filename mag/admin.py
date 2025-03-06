from django.contrib import admin
from . import models


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}



@admin.register(models.MagArticle)
class BlogPostAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'published')
    list_filter = ('published',)
    search_fields = ('title',)

# @admin.register(models.Comment)
# class CommentAdmin(admin.ModelAdmin):
#     list_display = ("__str__", "is_reply", "date", "status")
#     list_filter = ("status",)
#     list_editable = ('status',)
