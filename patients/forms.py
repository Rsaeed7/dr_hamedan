from django import forms
from .models import VisitEntry,MedicalRecord, MedicalReport, ReportImage

class VisitEntryForm(forms.ModelForm):
    class Meta:
        model = VisitEntry
        fields = [
            'visit_date',
            'chief_complaint',
            'diagnosis',
            'physical_exam',
            'treatment_plan',
            'prescribed_medications',
            'notes',
            'attachment',
        ]
        widgets = {
            'visit_date': forms.DateTimeInput(attrs={'type': 'datetime-local' }),
            'chief_complaint': forms.Textarea(attrs={'rows': 2 , 'class': 'w-full rounded border'}),
            'diagnosis': forms.Textarea(attrs={'rows': 2, 'class': 'w-full rounded border' }),
            'physical_exam': forms.Textarea(attrs={'rows': 2 , 'class': 'w-full rounded border'}),
            'treatment_plan': forms.Textarea(attrs={'rows': 2 , 'class': 'w-full rounded border'}),
            'prescribed_medications': forms.Textarea(attrs={'rows': 2 , 'class': 'w-full rounded border'}),
            'notes': forms.Textarea(attrs={'rows': 2 , 'class': 'w-full rounded border'}),
        }


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        exclude = ['doctor', 'patient']  # چون از view ست می‌کنیم
        widgets = {
            'symptoms': forms.Textarea(attrs={'rows': 3, 'class': 'w-full rounded border'}),
            'diagnosis': forms.Textarea(attrs={'rows': 3, 'class': 'w-full rounded border'}),
            'treatment': forms.Textarea(attrs={'rows': 3, 'class': 'w-full rounded border'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'w-full rounded border'}),
        }
        labels = {
            'symptoms': 'علائم',
            'diagnosis': 'تشخیص',
            'treatment': 'درمان',
            'notes': 'یادداشت پزشک',
        }


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True  # اجازه انتخاب چند فایل

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not data and initial:
            return initial
        return [super().clean(d, initial) for d in data]

class ReportForm(forms.ModelForm):
    name = forms.CharField(
        label="نام بیمار",
        widget=forms.TextInput(attrs={'class': 'px-4 py-2 border border-gray-300 rounded-md', 'placeholder': 'نام بیمار'})
    )
    title = forms.CharField(
        label="موضوع",
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md', 'placeholder': 'موضوع ریپورت'})
    )
    content = forms.CharField(
        label="شرح",
        widget=forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md', 'rows': 5, 'placeholder': 'شرح ریپورت'})
    )
    images = MultipleFileField(label="تصاویر گزارش", required=False)
    dr_requesting = forms.CharField(label="پزشک درخواست کننده", required=False,
                                    widget=forms.TextInput(attrs={'class': 'px-4 py-2 border border-gray-300 rounded-md', 'placeholder': 'نام پزشک درخواست کننده'})
                                    )
    age = forms.IntegerField(
        label="سن بیمار",
        required=False,
        widget=forms.NumberInput(
            attrs={'class': 'px-4 py-2 border border-gray-300 rounded-md', 'placeholder': 'سن بیمار'})
    )

    class Meta:
        model = MedicalReport
        fields = ['title', 'content', 'dr_requesting', 'age']

    def __init__(self, *args, **kwargs):
        patient_name = kwargs.pop('patient_name', None)
        patient_age = kwargs.pop('patient_age', None)  # دریافت سن بیمار از ویو
        super().__init__(*args, **kwargs)

        if patient_name:
            self.fields['name'].initial = patient_name  # مقدار اولیه نام بیمار
        if patient_age:
            self.fields['age'].initial = patient_age  # مقدار اولیه سن بیمار

    def save(self, commit=True):
        report = super().save(commit=commit)
        if self.cleaned_data.get('images'):
            for image in self.cleaned_data['images']:
                ReportImage.objects.create(
                    report=report,
                    image=image,
                    caption=f"تصویر گزارش {report.title}"
                )
        return report