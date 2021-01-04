"""SecureSite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from website.views import *
from django.contrib.auth import views as auth_views
urlpatterns = [
    # path('afad8cd1-1edc-458e-b2e7-66c31ca0d4dd.txt', test, name='test'),
    path('admin/', admin.site.urls),
    path('cookies/', include('cookie_consent.urls')),
    path('', welcome, name="welcome"),
    path('login', login_user, name="login"),
    path('privacy_policy', privacy_policy, name="privacy_policy"),
    path('logout', logout_user, name="logout"),
    path('signup', signup, name="signup"),
    path('change_password', change_password, name="change_password"),
    path('profile', profile, name='profile'),
    path('download_info', download_info, name='download_info'),
    path('delete_profile', delete_profile, name='delete_profile'),
    path('edit_profile/<int:pk>/', ProfileView.as_view(), name='edit_profile'),
    path('meetings/', include('meetings.urls')),
    path('password-reset/', auth_views.PasswordResetView.as_view(
             template_name='website/password_reset/password_reset_form.html',
             subject_template_name='website/password_reset/password_reset_subject.txt',
             email_template_name='website/password_reset/password_reset_email.html',
             # success_url='/login/'
         ),
         name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
             template_name='website/password_reset/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
             template_name='website/password_reset/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
             template_name='website/password_reset/password_reset_complete.html'),
         name='password_reset_complete'),
    path('activate/<uidb64>/<token>/', ActivateAccount.as_view(), name='activate'),
]
