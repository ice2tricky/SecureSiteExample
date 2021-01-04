from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from datetime import datetime
from meetings.models import Meeting
from django.contrib.auth import authenticate, logout, login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django.contrib.auth.models import User
from website.forms import SignUpForm, LoginForm, ProfileForm
from django.forms import modelform_factory
from django.conf import settings
from urllib import request as url_request, parse
import json
from django.views.decorators.cache import never_cache
from django.views.generic import UpdateView, View
from django.urls import reverse_lazy
import csv

from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from website.tokens import account_activation_token


@never_cache
def welcome(request):
    # return render(request, "website/welcome.html", {"num_meetings": Meeting.objects.count()})
    return render(request, "website/welcome.html", {"meetings": Meeting.objects.all().order_by('date').filter(date__gte=datetime.today())})


@never_cache
def privacy_policy(request):
    return render(request, "website/privacy_policy.html")


@never_cache
def signup(request):
    if request.method == 'POST':
        result = check_captcha(request)
        print(result)
        # result will be a dict containing 'success' and 'action'.
        if (not result['success']) or (not result['action'] == 'form'):
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            form = SignUpForm()
            return render(request, "website/signup.html", {'form': form, "site_key": settings.RECAPTCHA_SITE_KEY})
        # form = UserCreationForm(request.POST)
        form = SignUpForm(request.POST)
        if form.is_valid():
            # form.save()
            # username = form.cleaned_data.get('username')
            # raw_password = form.cleaned_data.get('password1')
            # user = authenticate(username=username, password=raw_password)
            # login(request, user)
            # return redirect('/')

            # verification email
            user = form.save(commit=False)
            user.is_active = False  # Deactivate account till it is confirmed
            user.save()

            current_site = get_current_site(request)
            subject = 'Activate Your SecureSite Account'
            message = render_to_string('website/activation_email/account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            user.email_user(subject, message)

            messages.error(request, 'Please Confirm your email to complete registration.')

            return redirect('/')
    else:
        # form = UserCreationForm()
        form = SignUpForm()
    return render(request, 'website/signup.html', {'form': form, "site_key": settings.RECAPTCHA_SITE_KEY})


# LoginForm = modelform_factory(User, exclude=["password2"])


@never_cache
def login_user(request):
    if request.method == 'POST':
        result = check_captcha(request)

        # result will be a dict containing 'success' and 'action'.
        if (not result['success']) or (not result['action'] == 'form'):
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            form = AuthenticationForm()
            return render(request, "website/login.html", {'form': form, "site_key": settings.RECAPTCHA_SITE_KEY})

        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password, request=request)
        if user is None:
            try:
                uid = User.objects.get(username=username)
                print(uid)
                if uid.is_active:
                    messages.error(request, "Your username and password didn't match.Please try again.")
                else:
                    messages.error(request, "Activate your account through the link send to your email.")
            except User.DoesNotExist:
                messages.error(request, "Your username and password didn't match.Please try again.")
            form = AuthenticationForm(request.POST)
            return render(request, "website/login.html", {'form': form, "site_key": settings.RECAPTCHA_SITE_KEY})
        else:
            login(request, user)
            if user.is_staff:
                return redirect('/admin')

            return redirect('/')
    form = AuthenticationForm()
    return render(request, "website/login.html", {'form': form, "site_key": settings.RECAPTCHA_SITE_KEY})


def check_captcha(request):
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
    if result['success']:
        if result['score'] < 0.8:
            result['success'] = False
    return result


@never_cache
def logout_user(request):
    logout(request)
    return redirect('/')


@never_cache
def change_password(request):
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)
    if request.method == 'POST':
        result = check_captcha(request)

        # result will be a dict containing 'success' and 'action'.
        if (not result['success']) or (not result['action'] == 'form'):
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            form = LoginForm()
            return render(request, "website/change_password.html", {'form': form, "site_key": settings.RECAPTCHA_SITE_KEY})
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
    return render(request, 'website/change_password.html', {'form': form, "site_key": settings.RECAPTCHA_SITE_KEY})


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


class ActivateAccount(View):

    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.profile.email_confirmed = True
            user.save()
            login(request, user)
            messages.success(request, 'Your account have been confirmed.')
            return redirect('/')
        else:
            messages.warning(request, 'The confirmation link was invalid, possibly because it has already been used.')
            return redirect('/')


@never_cache
def delete_profile(request):
    if not request.is_authenticated:
        return HttpResponse('Unauthorized', status=401)
    if request.method == "POST":
        # delete object
        request.user.delete()
        messages.success(request, 'Profile has been deleted')
        return redirect("/")

    return render(request, "website/delete_profile.html")


@never_cache
def download_info(request):
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="information.csv"'

    writer = csv.writer(response)
    writer.writerow(['firstname:', request.user.first_name])
    writer.writerow(['lastname:', request.user.last_name])
    writer.writerow(['email:', request.user.email])
    writer.writerow(['username:', request.user.username])
    return response
