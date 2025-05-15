from django import forms
from .models import Doctor, Email


class EmailForm(forms.ModelForm):
    search_doctor = forms.CharField(
        label='جستجوی پزشک',
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'جستجو با نام یا تخصص...',
            'hx-get': '/doctors/search/',
            'hx-target': '#doctor-results',
            'hx-trigger': 'keyup changed delay:300ms',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'
        })
    )

    class Meta:
        model = Email
        fields = ['search_doctor', 'recipient', 'subject', 'body', 'is_important']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5, 'class': 'border'}),
            'subject': forms.TextInput(attrs={'class': 'border'}),
            'is_important': forms.CheckboxInput(attrs={'class': 'border'}),
        }
        labels = {
            'recipient': 'پزشک گیرنده',
            'subject': 'موضوع نامه',
            'body': 'متن نامه',
            'is_important': 'نامه مهم',
        }

    def __init__(self, *args, **kwargs):
        self.current_doctor = kwargs.pop('current_doctor', None)
        super().__init__(*args, **kwargs)
        self.fields['recipient'].widget = forms.HiddenInput()

        if self.current_doctor:
            self.fields['recipient'].queryset = Doctor.objects.filter(
                is_available=True
            ).exclude(id=self.current_doctor.id).select_related('user', 'specialization')

            self.fields['recipient'].widget.attrs.update({'class': 'form-select'})
            self.fields['recipient'].label_from_instance = lambda obj: (
                f"{obj.user.get_full_name()} - {getattr(obj.specialization, 'name', 'بدون تخصص')}"
            )

    def clean_recipient(self):
        recipient = self.cleaned_data.get('recipient')
        if recipient == self.current_doctor:
            raise forms.ValidationError("شما نمی‌توانید برای خودتان نامه ارسال کنید.")
        return recipient