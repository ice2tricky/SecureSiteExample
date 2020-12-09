from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Meeting, Room
from django.forms import modelform_factory
from .forms import MeetingForm
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
import datetime


@never_cache
def detail(request, id):
    # meeting = Meeting.objects.get(pk=id)
    meeting = get_object_or_404(Meeting, pk=id)
    return render(request, "meetings/detail.html", {"meeting": meeting})


@never_cache
def rooms(request):
    # meeting = Meeting.objects.get(pk=id)
    return render(request, "meetings/rooms.html", {"rooms": Room.objects.all()})


# standard
# MeetingForm = modelform_factory(Meeting, exclude=[])


@never_cache
def new(request):
    if not request.user.is_authenticated or request.user.is_staff:
        return HttpResponse('Unauthorized', status=401)
    if request.method == "POST":
        form = MeetingForm(request.POST)
        if form.is_valid():
            meeting_obj = form.save(commit=False)
            meeting_obj.user = request.user
            meeting_obj.save()
            messages.success(request, 'Meeting added')
            return redirect("welcome")
    else:
        form = MeetingForm()
    return render(request, "meetings/new.html", {"form": form})


@never_cache
def delete(request, id):
    if request.method == "POST":
        # delete object
        obj = get_object_or_404(Meeting, id=id)
        if obj.user == request.user or request.user.is_staff:
            obj.delete()
            messages.success(request, 'Meeting has been deleted')
            return redirect("/")
        else:
            return HttpResponse('Unauthorized', status=401)

    return render(request, "meetings/delete.html", {"id": id})


@never_cache
def edit(request, id):
    meeting = get_object_or_404(Meeting, id=id)
    if request.method == "POST":
        if meeting.user == request.user or request.user.is_staff:
            form = MeetingForm(request.POST, instance=meeting)
            if form.is_valid():
                Meeting.objects.update()
                meeting_obj = form.save(commit=False)
                meeting_obj.user = request.user
                meeting_obj.save()
                messages.success(request, 'Meeting has been changed')
                return redirect("/")
            else:
                messages.error(request, 'Please correct the error below.')
        else:
            return HttpResponse('Unauthorized', status=401)
    if meeting.date >= datetime.date.today():
        form = MeetingForm(None, instance=meeting)
        return render(request, "meetings/edit.html", {"form": form})
    else:
        return HttpResponse('Unauthorized', status=401)
