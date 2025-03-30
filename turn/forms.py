from django import forms





class ReservationForm(forms.Form):
    name = forms.CharField(max_length=100,widget=forms.TextInput(attrs={'class': 'form-control my-2', 'placeholder': 'نام و نام خانوادگی '}))
    phone = forms.CharField(max_length=11,widget=forms.NumberInput(attrs={'class': 'form-control my-2', 'placeholder': 'شماره تلفن '}))
    meli_code = forms.CharField(max_length=11,widget=forms.NumberInput(attrs={'class': 'form-control my-2', 'placeholder': 'کد ملی '}))

