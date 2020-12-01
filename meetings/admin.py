from django.contrib import admin
from .models import Meeting
from .models import Room

# Register your models here.

admin.site.register(Meeting)
admin.site.register(Room)
