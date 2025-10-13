from django import forms
from django_jalali.forms import jDateField
from .models import HomeCareRequest

class HomeCareRequestForm(forms.ModelForm):
    first_name = forms.CharField(label="نام", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="نام خانوادگی", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    requested_date = forms.HiddenInput()

    class Meta:
        model = HomeCareRequest
        fields = ['requested_date', 'requested_time', 'city', 'address', 'extra_notes', 'prescription_file']
        widgets = {
            'requested_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control col-6'}),
            'city': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'extra_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'prescription_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'requested_date': forms.HiddenInput(),
        }
        labels = {
            'requested_time': 'ساعت حدودی مورد نظر',
            'city': 'شهر',
            'address': 'آدرس دقیق',
            'extra_notes': 'توضیحات اضافی',
            'prescription_file': 'نسخه پزشکی',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        service = kwargs.pop('service', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name

        if service:
            self.fields['city'].queryset = service.available_in_cities.all()

    def save(self, commit=True):
        instance = super().save(commit=False)

        user = getattr(self, 'user', None)
        if user:
            user.first_name = self.cleaned_data.get('first_name', user.first_name)
            user.last_name = self.cleaned_data.get('last_name', user.last_name)
            user.save()

        if commit:
            instance.save()
        return instance