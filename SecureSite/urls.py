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
    path('admin/', admin.site.urls),
    path('', welcome, name="welcome"),
    path('username', username, name="username"),
    path('login', login_user, name="login"),
    path('logout', logout_user, name="logout"),
    path('signup', signup, name="signup"),
    path('change-password/', auth_views.PasswordChangeView.as_view(
            template_name='website/change_password.html',
            success_url='/'
        ), name="change_password"),
    path('profile', profile, name='profile'),
    path('edit_profile/<int:pk>/', ProfileView.as_view(), name='edit_profile'),
    path('meetings/', include('meetings.urls')),
]
