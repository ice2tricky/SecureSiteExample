from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse
from datetime import datetime
from meetings.models import Meeting
from django.contrib.auth import authenticate, logout, login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from website.forms import SignUpForm, LoginForm, ProfileForm
from django.forms import modelform_factory
from django.conf import settings
from urllib import request as url_request, parse
import json
from django.views.decorators.cache import never_cache
from django.views.generic import UpdateView
from django.urls import reverse_lazy


@never_cache
def welcome(request):
    # return render(request, "website/welcome.html", {"num_meetings": Meeting.objects.count()})
    return render(request, "website/welcome.html", {"meetings": Meeting.objects.all()})


@never_cache
def signup(request):
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
        if (not result['success']) or (not result['action'] == 'form'):
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            form = SignUpForm()
            return render(request, "website/signup.html", {'form': form, "site_key": settings.RECAPTCHA_SITE_KEY})
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
    return render(request, 'website/signup.html', {'form': form, "site_key": settings.RECAPTCHA_SITE_KEY})


# LoginForm = modelform_factory(User, exclude=["password2"])


@never_cache
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
        if (not result['success']) or (not result['action'] == 'form'):
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            form = LoginForm()
            return render(request, "website/login.html", {'form': form, "site_key": settings.RECAPTCHA_SITE_KEY})

        username = request.POST['username']
        password = request.POST['password1']
        user = authenticate(username=username, password=password)
        if user is None:
            form = LoginForm(request.POST)
            return render(request, "website/login.html", {'form': form, "site_key": settings.RECAPTCHA_SITE_KEY})
        else:
            login(request, user)
            if user.is_staff:
                return redirect('/admin')

            return redirect('/')
    form = LoginForm()
    return render(request, "website/login.html", {'form': form, "site_key": settings.RECAPTCHA_SITE_KEY})


@never_cache
def logout_user(request):
    logout(request)
    return redirect('/')


@never_cache
def username(request):
    return HttpResponse("Username is " + request.user.username)


@never_cache
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'website/change_password.html', {
        'form': form
    })


@never_cache
def profile(request):
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)
    return render(request, "website/profile.html")


# Edit Profile View
class ProfileView(UpdateView):
    model = User
    form_class = ProfileForm
    success_url = reverse_lazy('profile')
    template_name = 'website/edit_profile.html'

