from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout
)

from .forms import UserLoginForm, UserRegisterForm, UserForgotForm, UserResetForm
from adminApp.email import encrypt, decrypt, sendResetEmail, sendSignupEmail
User = get_user_model()

def login_view(request):
    next = request.GET.get('next')
    form = UserLoginForm(request.POST or None)
    if form.is_valid():
        email = form.cleaned_data.get('email')
        username = User.objects.get(email=email.lower()).username
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        login(request, user)
        # If is_staff move to dashboard
        if user.is_staff:
            return redirect('adminDashboard')

        if next:
            return redirect(next)
        return redirect('/')

    context = {
        'form': form,
    }
    return render(request, "Log in.html", context)


def register_view(request):
    next = request.GET.get('next')
    enc_username = request.GET.get('ecna', '')
    enc_email = request.GET.get('ecto', '')
    print(enc_username, enc_email)
    username = decrypt(enc_username)
    email = decrypt(enc_email)
    if username == '' or email == '':
        return redirect('/')

    form = UserRegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        password = form.cleaned_data.get('password')
        user.username = user.email
        user.set_password(password)
        user.save()
        sendSignupEmail(email, username)
        new_user = authenticate(username=user.username, password=password)
        login(request, new_user)
        if next:
            return redirect(next)
        return redirect('/')
    print(form.errors)
    print('------>register initial values', username, email)
    form.initial['first_name'] = username
    form.initial['email'] = email

    context = {
        'form': form,
    }
    return render(request, "Register.html", context)


def logout_view(request):
    logout(request)
    return redirect('/')

def forgot_view(request):
    form = UserForgotForm(request.POST or None)
    if form.is_valid():
        email = form.cleaned_data.get('email')
        username = User.objects.get(email=email.lower()).username
        sendResetEmail(email, username)
        return render(request, "Email Confirm.html", {'email':email})

    return render(request, "Forgot Password.html", {'form':form})

def reset_view(request):
    enc_username = request.GET.get('ecna', '')
    enc_email = request.GET.get('ecto', '')
    # print(enc_username, enc_email)
    username = decrypt(enc_username)
    email = decrypt(enc_email)

    form = UserResetForm(request.POST or None)
    if email != '':
        form.initial['email'] = email

    if form.is_valid():
        password = form.cleaned_data.get('password')
        user = User.objects.filter(email=email.lower())[0]
        user.set_password(password)
        user.save()
        try:
            new_user = authenticate(username=user.username, password=password)
            login(request, new_user)
            return redirect('/')
        except Exception as error:
            print('[SPIDER] [Accounts] Reset Password Exception Log In Error : ' + repr(error)) 
            return redirect('/')
    return render(request, "Reset Password.html", {'form':form})

def confirm_view(request):
    return render(request, "Email Confirm.html", {'email':'fastcodespider@gmail.com'})
