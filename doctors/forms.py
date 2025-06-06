from django import forms
from .models import Doctor, Email, DoctorRegistration, Specialization, City


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


class DoctorRegistrationForm(forms.ModelForm):
    """Form for doctor registration applications"""
    
    class Meta:
        model = DoctorRegistration
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'national_id', 'gender',
            'specialization', 'license_number', 'city', 'bio', 'consultation_fee',
            'consultation_duration', 'profile_image', 'license_image', 'degree_image'
        ]
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'نام'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'نام خانوادگی'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'ایمیل'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'شماره تماس'
            }),
            'national_id': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'کد ملی'
            }),
            'gender': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            }),
            'specialization': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            }),
            'license_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'شماره پروانه'
            }),
            'city': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'بیوگرافی و تجربیات کاری',
                'rows': 4
            }),
            'consultation_fee': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'هزینه ویزیت (تومان)'
            }),
            'consultation_duration': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'مدت زمان ویزیت (دقیقه)',
                'min': '15',
                'max': '120'
            }),
            'profile_image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'accept': 'image/*'
            }),
            'license_image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'accept': 'image/*'
            }),
            'degree_image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'accept': 'image/*'
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists in user table or pending registrations
            from user.models import User
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("این ایمیل قبلاً استفاده شده است.")
            if DoctorRegistration.objects.filter(email=email, status='pending').exists():
                raise forms.ValidationError("درخواست عضویت با این ایمیل در حال بررسی است.")
        return email
    
    def clean_national_id(self):
        national_id = self.cleaned_data.get('national_id')
        if national_id:
            # Check if national ID already exists
            from user.models import User
            if User.objects.filter(national_id=national_id).exists():
                raise forms.ValidationError("این کد ملی قبلاً استفاده شده است.")
            if DoctorRegistration.objects.filter(national_id=national_id, status='pending').exists():
                raise forms.ValidationError("درخواست عضویت با این کد ملی در حال بررسی است.")
        return national_id
    
    def clean_license_number(self):
        license_number = self.cleaned_data.get('license_number')
        if license_number:
            # Check if license number already exists
            if Doctor.objects.filter(license_number=license_number).exists():
                raise forms.ValidationError("این شماره پروانه قبلاً استفاده شده است.")
            if DoctorRegistration.objects.filter(license_number=license_number, status='pending').exists():
                raise forms.ValidationError("درخواست عضویت با این شماره پروانه در حال بررسی است.")
        return license_number