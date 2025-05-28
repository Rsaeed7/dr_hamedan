from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User,Otp
from .forms import UserChangeForm,UserCreationForm




class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ['phone', "is_admin"]
    list_filter = ["is_admin"]
    fieldsets = [
        (None, {"fields": ["phone", "password"]}),
        ("اطلاعات شخصی", {"fields": ['first_name','last_name','email']}),
        ("دسترسی ها", {"fields": ["is_admin" , 'is_staff' , 'is_superuser','is_admin_chat'] }),
    ]
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": ["phone", "password1", "password2"],
            },
        ),
    ]
    search_fields = ["phone",'email']
    ordering = ["phone"]
    filter_horizontal = []


admin.site.register(User, UserAdmin)
admin.site.register(Otp)
admin.site.unregister(Group)