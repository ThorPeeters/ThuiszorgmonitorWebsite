from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.contrib.auth.forms import AuthenticationForm

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'age', 'emergencyContact1', 'emergencyContact2', 'password1', 'password2')
        labels = {
            'emergencyContact1': 'Number emergency contact 1',
            'emergencyContact2': 'Number emergency contact 2',
        }

class CustomLoginForm(AuthenticationForm):
    pass  # Dit kan de standaard form zijn, tenzij je extra validatie wilt

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'age', 'emergencyContact1', 'emergencyContact2']

