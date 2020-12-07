from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse
from datetime import datetime
from meetings.models import Meeting
from django.contrib.auth import authenticate, logout, login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from website.forms import SignUpForm, LoginForm
from django.forms import modelform_factory
from django.conf import settings
from urllib import request as url_request, parse
import json


def welcome(request):
    # return render(request, "website/welcome.html", {"num_meetings": Meeting.objects.count()})
    return render(request, "website/welcome.html", {"meetings": Meeting.objects.all()})


def signup(request):
    if request.method == 'POST':
        # form = UserCreationForm(request.POST)
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('/')
    else:
        # form = UserCreationForm()
        form = SignUpForm()
    return render(request, 'website/signup.html', {'form': form})


# LoginForm = modelform_factory(User, exclude=["password2"])


def login_user(request):
    if request.method == 'POST':
        # get the token submitted in the form
        recaptcha_response = request.POST.get('g-recaptcha-response')
        url = 'https://www.google.com/recaptcha/api/siteverify'
        payload = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        data = parse.urlencode(payload).encode()
        req = url_request.Request(url, data=data)

        # verify the token submitted with the form is valid
        response = url_request.urlopen(req)
        result = json.loads(response.read().decode())

        # result will be a dict containing 'success' and 'action'.
        print(result)
        if (not result['success']) or (not result['action'] == 'login_form'):
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            form = LoginForm()
            return render(request, "website/login.html", {'form': form, "site_key": settings.RECAPTCHA_SITE_KEY})

        username = request.POST['username']
        password = request.POST['password1']
        user = authenticate(username=username, password=password)
        if user is None:
            form = LoginForm(request.POST)
            render(request, "website/login.html", {'form': form, "site_key": settings.RECAPTCHA_SITE_KEY})
        else:
            login(request, user)
            if user.is_staff:
                return redirect('/admin')

            return redirect('/')
    form = LoginForm()
    return render(request, "website/login.html", {'form': form, "site_key": settings.RECAPTCHA_SITE_KEY})


def logout_user(request):
    logout(request)
    return redirect('/')


def username(request):
    return HttpResponse("Username is " + request.user.username)


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'website/change_password.html', {
        'form': form
    })
