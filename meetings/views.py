from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Meeting, Room
# from django.forms import modelform_factory
from .forms import MeetingForm
from django.http import HttpResponse
from django.views.decorators.cache import never_cache


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
    # request.user.username
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)
    if request.method == "POST":
        form = MeetingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Meeting added')
            return redirect("welcome")
    else:
        form = MeetingForm()
    return render(request, "meetings/new.html", {"form": form})


@never_cache
def delete(request, id):
    if request.method == "POST":
        print(id)
        print(request.POST)
        # delete object
        obj = get_object_or_404(Meeting, id=id)
        if obj.user == request.user:
            obj.delete()
            messages.success(request, 'Meeting has been deleted')
            return redirect("/")
        else:
            return HttpResponse('Unauthorized', status=401)

    return render(request, "meetings/delete.html", {"id": id})


@never_cache
def edit(request, id):
    if request.method == "POST":
        form = MeetingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Meeting has been changed')
            return redirect("/")
        else:
            return HttpResponse('Unauthorized', status=401)
    meeting = MeetingForm(get_object_or_404(Meeting, pk=id))
    return render(request, "meetings/edit.html", {"meeting": meeting})
