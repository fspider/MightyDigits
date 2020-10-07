from django import forms
from django.contrib.auth import (
    authenticate,
    get_user_model
)
User = get_user_model()

class UserRegisterForm(forms.ModelForm):
    DISPLAY_CHOICES = [
        (0,'Basic'),
        (1,'Admin')
        ]
    username = forms.CharField(widget=forms.EmailInput(attrs={
                                    'class':"w3-input",
                                    'type':"text",
                                    'placeholder':"First Name",
                                    'id':"newUserName",
                                }))

    email = forms.CharField(widget=forms.EmailInput(attrs={
                                    'class':"w3-input",
                                    'type':"email",
                                    'placeholder':"Email",
                                    'id':"newEmail",
                                }))

    isAdmin = forms.ChoiceField(widget=forms.RadioSelect(attrs={
                                   'name':"newUserPermissions",
                                }), choices=DISPLAY_CHOICES)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'isAdmin',
        ]

    def clean(self, *args, **kwargs):
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')

        email_qs = User.objects.filter(email=email)
        if email_qs.exists():
            raise forms.ValidationError(
                "This email has already been registered")
        email_qs = User.objects.filter(username=username)
        if email_qs.exists():
            raise forms.ValidationError(
                "This username has already been registered")

        return super(UserRegisterForm, self).clean(*args, **kwargs)
