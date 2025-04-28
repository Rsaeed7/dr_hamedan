from django import forms
from .models import ContactUs

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactUs
        fields = '__all__'
        widgets ={
            'name': forms.TextInput(attrs={'class':'form-control','placeholder': 'نام و نام حانوادگی'}),
            'email': forms.EmailInput(attrs={'class':'form-control','placeholder': 'ایمیل'}),
            'subject': forms.TextInput(attrs={'class':'form-control','placeholder': 'موضوع پیام'}),
            'message': forms.Textarea(attrs={'class':'form-control','cols':'30' ,'rows':'6','placeholder': 'پیام خودتان را بنویسید'})
        }