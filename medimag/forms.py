from django import forms
from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'text', 'gender', 'parent']  # فیلدهای موردنیاز
        widgets = {
            'name': forms.TextInput(attrs={
                'id': 'name',
                'class': 'form-control',
                'placeholder': 'نام خود را وارد کنید'
            }),
            'text': forms.Textarea(attrs={
                'id': 'text',
                'class': 'form-control',
                'cols': '100',
                'rows': '6',
                'placeholder': 'پیام خود را بنویسید'
            }),
            'gender': forms.RadioSelect(attrs={'class': 'custom-gender-toggle'}),
            'parent': forms.HiddenInput(attrs={'id': 'parent_id'}),
        }