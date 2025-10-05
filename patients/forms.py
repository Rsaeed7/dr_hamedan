from django import forms
from django_jalali.forms import jDateTimeField, jDateField
from .models import VisitEntry,MedicalRecord, MedicalReport, ReportImage,DrReportSettings,ReportTemplate

class VisitEntryForm(forms.ModelForm):
    
    class Meta:
        model = VisitEntry
        fields = [
            'chief_complaint',
            'diagnosis',
            'physical_exam',
            'treatment_plan',
            'prescribed_medications',
            'notes',
            'attachment',
            'handwritten_image',
        ]
        widgets = {
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
        exclude = ['doctor', 'patient']
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
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        default_attrs = {'multiple': True}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class ReportForm(forms.ModelForm):
    name = forms.CharField(
        label="نام بیمار",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'نام بیمار'
        })
    )

    age = forms.IntegerField(
        label="سن بیمار",
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'سن بیمار'
        })
    )

    title = forms.CharField(
        label="عنوان گزارش",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'عنوان گزارش'
        })
    )

    dr_requesting = forms.CharField(
        label="پزشک درخواست‌کننده",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'پزشک معالج یا درخواست‌کننده'
        })
    )

    content = forms.CharField(
        label="متن گزارش",
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 6,
            'placeholder': 'متن گزارش را وارد کنید...'
        })
    )

    # 🔥 تغییر اینجا - استفاده از MultipleFileField به جای FileField
    images = MultipleFileField(
        label="تصاویر پیوست",
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500',
            'accept': 'image/*'
        })
    )

    class Meta:
        model = MedicalReport
        fields = ['name', 'age', 'title', 'dr_requesting', 'content', 'images']

    def __init__(self, *args, **kwargs):
        patient_name = kwargs.pop('patient_name', None)
        patient_age = kwargs.pop('patient_age', None)
        super().__init__(*args, **kwargs)

        if patient_name:
            self.fields['name'].initial = patient_name
            self.fields['name'].widget.attrs['readonly'] = True
            self.fields['name'].widget.attrs['class'] += ' bg-gray-100 cursor-not-allowed'

        if patient_age:
            self.fields['age'].initial = patient_age
            self.fields['age'].widget.attrs['readonly'] = True
            self.fields['age'].widget.attrs['class'] += ' bg-gray-100 cursor-not-allowed'

    def save(self, commit=True):
        report = super().save(commit=commit)
        images = self.cleaned_data.get('images')
        if images:
            # اطمینان از اینکه images یک لیست است
            if not isinstance(images, (list, tuple)):
                images = [images]

            for image in images:
                ReportImage.objects.create(
                    report=report,
                    image=image,
                    caption=f"تصویر گزارش {report.title}"
                )
        return report

class EditReportForm(forms.ModelForm):
    class Meta:
        model = MedicalReport
        fields = ['title', 'name', 'age', 'dr_requesting', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'px-4 py-2 border border-gray-300 rounded-md'}),
            'name': forms.TextInput(attrs={'class': 'px-4 py-2 border border-gray-300 rounded-md'}),
            'age': forms.NumberInput(attrs={'class': 'px-4 py-2 border border-gray-300 rounded-md'}),
            'dr_requesting': forms.TextInput(attrs={'class': 'px-4 py-2 border border-gray-300 rounded-md'}),
            'content': forms.Textarea(attrs={'class': 'px-4 py-2 border border-gray-300 rounded-md', 'rows': 4}),
        }
        labels = {
            'title': 'نوع بررسی',
            'name': 'نام بیمار',
            'age': 'سن بیمار',
            'dr_requesting': 'پزشک معالج',
            'content': 'توضیحات گزارش',
        }


class DrReportSettingsForm(forms.ModelForm):
    class Meta:
        model = DrReportSettings
        fields = ['background_image',]
        labels = {
            'custom_css': 'استایل سفارشی',
        }


class ReportTemplateForm(forms.ModelForm):
    class Meta:
        model = ReportTemplate
        fields = ['title', 'dr_requesting', 'content']
        labels = {
            'title': 'عنوان قالب',
            'dr_requesting': 'پزشک معالج',
            'content': 'متن گزارش',
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'مثلاً: گزارش سونوگرافی شکم'
            }),
            'dr_requesting': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'نام پزشک درخواست‌کننده'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 6,
                'placeholder': 'متن گزارش را وارد کنید...'
            }),
        }
