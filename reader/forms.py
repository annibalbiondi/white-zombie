# coding=utf-8
from django import forms
from django.contrib.auth.models import User

class RegisterForm(forms.ModelForm):

    '''
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if not password2:
            raise forms.ValidationError("You must confirm your password")
        elif password1 != password2:
            raise forms.ValidationError("Your passwords do not match")
        return password2
    '''

    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'minlength': 1,
                'maxlength': 16
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),
            'password': forms.PasswordInput(attrs={
                'class': 'form-control',
                'minlength': '6',
                'maxlength': '16'
            })
        }

class LoginForm(forms.Form):
    username = forms.CharField(
        min_length=1,
        max_length=16,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuário',
        }))
    password = forms.CharField(
        min_length=1,
        max_length=16,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Senha',
        }))

class FeedSubscriptionForm(forms.Form):
    link = forms.URLField(
        widget=forms.URLInput(
            attrs={'placeholder': 'Endereço do Feed'}),
        label='')
