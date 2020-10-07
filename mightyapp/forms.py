from django import forms
from django.contrib.auth import (
    authenticate,
    get_user_model,
)

User = get_user_model()

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=100,
                                widget=forms.TextInput(attrs={
                                    'class':'form-control',
                                    'placeholder' : "Enter Username",
                                }))
    password = forms.CharField(max_length=100,
                                widget=forms.PasswordInput(attrs={
                                    'class':'form-control',
                                    'placeholder' : "Enter Password",
                                }))
    email = forms.CharField(max_length=100,
                                widget=forms.EmailInput(attrs={
                                    'class':'form-control',
                                    'placeholder' : "Enter Email",
                                }))
    phone = forms.CharField(max_length=100,
                                widget=forms.NumberInput(attrs={
                                    'class':'form-control',
                                    'placeholder' : "Enter Phone",
                                }))

class SigninForm(forms.Form):
    email = forms.CharField(max_length=100,
                                widget=forms.EmailInput(attrs={
                                    'class':"input-card",
                                    'type' : "email",
                                    'name' : "email",
                                    'id'   : "email",
                                    'placeholder' : "Please, Enter your email",
                                    'required' : 'required',
                                }))
    password = forms.CharField(max_length=100,
                                widget=forms.PasswordInput(attrs={
                                    'class':"input-card",
                                    'type' : "password",
                                    'name' : "password",
                                    'id'   : "password",
                                    'placeholder' : "Please, Enter your password",
                                    'required' : 'required',
                                }))
