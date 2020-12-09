from django.urls import path

from .views import *

urlpatterns = [
    path('delete/<int:id>', delete, name="delete"),
    path('edit/<int:id>', delete, name="edit"),
    path('<int:id>', detail, name="detail"),
    path('rooms', rooms, name="rooms"),
    path('new', new, name="new")
]