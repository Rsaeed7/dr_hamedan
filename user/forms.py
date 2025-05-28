from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from django.core import validators
from .models import User



class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""

    password1 = forms.CharField(label="گذرواژه", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="تکرار گذرواژه", widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ["phone",]

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    disabled password hash display field.
    """

    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ["phone", "password", "is_active", "is_admin"]

def phone_validator(value):
    if value[0] != '0':
        raise ValidationError("لطفا شماره تلفن صحیح وارد کنید")
    elif len(value) != 11:
        raise ValidationError('! شماره تلفن باید 11 رقم باشد')
class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={"class":"form-control unicase-form-control text-input","placeholder": "شماره تلفن یا ایمل خود را وارد کنید"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class":"form-control unicase-form-control text-input","placeholder": "رمز عبور خود را وارد کنید"}))

    # def clean_phone(self):
    #     phone = self.cleaned_data["phone"]
    #     if len(phone) != 11:
    #         raise ValidationError("شماره تلفن صحیح وارد کنید!",code='invalid_phone')
    #     return phone

class RegisterForm(forms.Form):
    phone = forms.CharField(widget=forms.TextInput(
        attrs={"class": "form-control required", "placeholder": "09*********"}),
                            validators=[phone_validator],required=True)

class Check_CodeForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "****"}),
                            validators=[validators.MinLengthValidator(4)],required=True)


