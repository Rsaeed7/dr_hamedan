# accounts/forms.py
from django import forms
# from django.contrib.auth.models import User
from user.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import UserProfile

# class RegisterForm(UserCreationForm):
#     email = forms.EmailField(
#         max_length=254,
#         required=True,
#         widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'}),
#         help_text=_('لطفا یک آدرس ایمیل معتبر وارد کنید.')
#     )
#
#     first_name = forms.CharField(
#         max_length=30,
#         required=True,
#         widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'})
#     )
#
#     last_name = forms.CharField(
#         max_length=30,
#         required=True,
#         widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'})
#     )
#
#     class Meta:
#         model = User
#         fields = ['name', 'email', 'first_name', 'last_name', 'password1', 'password2']
#         widgets = {
#             'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'}),
#             'password1': forms.PasswordInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'}),
#             'password2': forms.PasswordInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'}),
#         }
#
#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if User.objects.filter(email=email).exists():
#             raise forms.ValidationError(_('این آدرس ایمیل قبلا استفاده شده است.'))
#         return email
#
# class LoginForm(forms.Form):
#     name = forms.CharField(
#         widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'})
#     )
#     password = forms.CharField(
#         widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'})
#     )
#     remember_me = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'}))

# class ProfileForm(forms.ModelForm):
#     class Meta:
#         model = User
#         fields = ['name', 'email', 'first_name', 'last_name']
#         widgets = {
#             'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'}),
#             'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'}),
#             'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'}),
#             'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'}),
#         }

# class UserProfileForm(forms.ModelForm):
#
#     class Meta:
#         model = UserProfile
#         fields = ['phone_number', 'national_id', 'birth_date', 'address', 'profile_image']
#         widgets = {
#             'phone_number': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'}),
#             'national_id': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'}),
#             'birth_date': forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500', 'type': 'date'}),
#             'address': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500', 'rows': 3}),
#             'profile_image': forms.FileInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'}),
#         }