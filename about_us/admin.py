from django.contrib import admin
from .models import Contact,ContactUs,Message
admin.site.register(Contact)
admin.site.register(ContactUs)
# admin.site.register(Message)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("message", "published")
    list_editable = ('published',)

# Register your models here.
