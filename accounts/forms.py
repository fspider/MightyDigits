from django import forms
from django.contrib.auth import (
    authenticate,
    get_user_model

)
User = get_user_model()
from django.contrib.auth.validators import UnicodeUsernameValidator

class UserLoginForm(forms.Form):
    email = forms.CharField(max_length=100,
                                widget=forms.EmailInput(attrs={
                                    'class': "w3-input",
                                    'type': "email",
                                    'name': "email",
                                    'placeholder': "Email",
                                    'required' : 'required',
                                }))

    password = forms.CharField(max_length=100,
                                widget=forms.PasswordInput(attrs={
                                    'class': "w3-input",
                                    'type': "password",
                                    'name': "password",
                                    'placeholder': "Password",
                                    'required' : 'required',
                                }))

    def clean(self, *args, **kwargs):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            try:
                username = User.objects.get(email=email.lower()).username
                user = authenticate(username=username, password=password)
            except:
                raise forms.ValidationError('This user does not exist')
            if not user:
                raise forms.ValidationError('Incorrect password')
            if not user.check_password(password):
                raise forms.ValidationError('Incorrect password')
            if not user.is_active:
                raise forms.ValidationError('This user is not active')
        return super(UserLoginForm, self).clean(*args, **kwargs)


class UserRegisterForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100,
                                widget=forms.TextInput(attrs={
                                    'class':"w3-input",
                                    'type':"text",
                                    'placeholder':"First Name",
                                    'required':"required",
                                }))

    email = forms.CharField(max_length=100,
                                widget=forms.EmailInput(attrs={
                                    'class': "w3-input",
                                    'type': "email",
                                    'name': "email",
                                    'placeholder': "Email",
                                    'required' : 'required',
                                }))

    password = forms.CharField(max_length=100,
                                widget=forms.PasswordInput(attrs={
                                    'class': "w3-input",
                                    'type': "password",
                                    'name': "password",
                                    'placeholder': "Password",
                                    'required' : 'required',
                                }))
    confirmPassword = forms.CharField(max_length=100,
                                widget=forms.PasswordInput(attrs={
                                    'class': "w3-input",
                                    'type': "password",
                                    'name': "confirmPassword",
                                    'placeholder': "Confirm Password",
                                    'required' : 'required',
                                }))

    class Meta:
        model = User
        fields = [
            'first_name',
            'email',
            'password',
            'confirmPassword'
        ]

    def clean(self, *args, **kwargs):
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        confirmPassword = self.cleaned_data.get('confirmPassword')
        print('-------------------------------->')
        if password != confirmPassword:
            raise forms.ValidationError("Password must match")

        # username_qs = User.objects.filter(username=username)
        # if username_qs.exists():
        #     raise forms.ValidationError(
        #         "This username has already been registered")

        email_qs = User.objects.filter(email=email)
        if email_qs.exists():
            raise forms.ValidationError(
                "This email has already been registered")

        return super(UserRegisterForm, self).clean(*args, **kwargs)


class UserForgotForm(forms.ModelForm):
    email = forms.CharField(max_length=100,
                                widget=forms.EmailInput(attrs={
                                    'class': "w3-input",
                                    'type': "email",
                                    'name': "email",
                                    'placeholder': "Email",
                                    'required' : 'required',
                                }))

    class Meta:
        model = User
        fields = [
            'email',
        ]

    def clean(self, *args, **kwargs):
        email = self.cleaned_data.get('email')

        email_qs = User.objects.filter(email=email)
        if not email_qs.exists():
            raise forms.ValidationError(
                "This email not exists!")

        return super(UserForgotForm, self).clean(*args, **kwargs)


class UserResetForm(forms.ModelForm):

    password = forms.CharField(max_length=100,
                                widget=forms.PasswordInput(attrs={
                                    'class': "w3-input",
                                    'type': "password",
                                    'name': "password",
                                    'placeholder': "Password",
                                    'required' : 'required',
                                }))
    confirmPassword = forms.CharField(max_length=100,
                                widget=forms.PasswordInput(attrs={
                                    'class': "w3-input",
                                    'type': "password",
                                    'name': "confirmPassword",
                                    'placeholder': "Confirm Password",
                                    'required' : 'required',
                                }))

    class Meta:
        model = User
        fields = [
            'password',
            'confirmPassword'
        ]

    def clean(self, *args, **kwargs):
        password = self.cleaned_data.get('password')
        confirmPassword = self.cleaned_data.get('confirmPassword')

        if password != confirmPassword:
            raise forms.ValidationError("Password must match")

        return super(UserResetForm, self).clean(*args, **kwargs)