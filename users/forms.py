from django import forms
from django.contrib.auth.models import User
from .models import PhotographerProfile, Photo, BookingRequest, ClientProfile


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Повторите пароль")
    is_photographer = forms.BooleanField(required=False, widget=forms.HiddenInput(), label="Я фотограф")

    class Meta:
        model = User
        fields = ['username', 'email']
        help_texts = {
            'username': '',
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            self.add_error('confirm_password', "Пароли не совпадают")
        return cleaned_data


class PhotographerProfileForm(forms.ModelForm):
    first_name = forms.CharField(label="Имя", required=False)
    last_name = forms.CharField(label="Фамилия", required=False)
    email = forms.EmailField(label="Email", required=True)

    class Meta:
        model = PhotographerProfile
        fields = ['first_name', 'last_name', 'email', 'short_intro', 'bio', 'city', 'specialization', 'price', 'language', 'profile_image']
        labels = {
            'short_intro': 'Кратко о себе',
            'bio': 'Биография',
            'city': 'Город',
            'specialization': 'Специализация',
            'price': 'Стоимость часа (RUB)',
            'language': 'Язык',
            'profile_image': 'Фото профиля'
        }
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'short_intro': forms.TextInput(attrs={'placeholder': 'Например: Свадебный фотограф в Москве'}),
            'price': forms.NumberInput(attrs={'class': 'form-control price-input', 'placeholder': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super(PhotographerProfileForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super(PhotographerProfileForm, self).save(commit=False)
        if commit:
            profile.save()
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
        return profile


class PhotoUploadForm(forms.Form):
    image = forms.ImageField(widget=forms.ClearableFileInput(), label='Загрузить фото')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].widget.attrs.update({'multiple': True})


class ClientProfileForm(forms.ModelForm):
    first_name = forms.CharField(label="Имя", required=False)
    last_name = forms.CharField(label="Фамилия", required=False)
    email = forms.EmailField(label="Email", required=True)

    class Meta:
        model = ClientProfile
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_image']
        labels = {
            'phone_number': 'Номер телефона',
            'profile_image': 'Фото профиля'
        }
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': '+7 (999) 000-00-00'}),
        }

    def __init__(self, *args, **kwargs):
        super(ClientProfileForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super(ClientProfileForm, self).save(commit=False)
        if commit:
            profile.save()
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
        return profile


class BookingRequestForm(forms.ModelForm):
    class Meta:
        model = BookingRequest
        fields = ['message', 'contact_phone']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Опишите ваше событие (дата, место, пожелания)...'}),
            'contact_phone': forms.TextInput(attrs={
                'placeholder': '+ 7 999 999 99 99', 
                'id': 'phone-input',
                'pattern': r'\+ 7 \d{3} \d{3} \d{2} \d{2}',
                'minlength': '17',
                'maxlength': '17'
            }),
        }

    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone')
        import re
        pattern = re.compile(r'^\+ 7 \d{3} \d{3} \d{2} \d{2}$')
        if not pattern.match(phone):
            raise forms.ValidationError("Введите корректный номер телефона в формате + 7 999 999 99 99")
        return phone

