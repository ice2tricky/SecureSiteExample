from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse
from datetime import datetime
from meetings.models import Meeting
from django.contrib.auth import authenticate, logout, login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from website.forms import SignUpForm, LoginForm
from django.forms import modelform_factory


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
        username = request.POST['username']
        password = request.POST['password1']
        user = authenticate(username=username, password=password)
        if user is None:
            form = LoginForm(request.POST)
            render(request, "website/login.html", {'form': form})
        else:
            login(request, user)
            if user.is_staff:
                return redirect('/admin')

            return redirect('/')
    form = LoginForm()
    return render(request, "website/login.html", {'form': form})


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
