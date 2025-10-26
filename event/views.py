from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse
from django.core import serializers
from django.shortcuts import render, redirect, get_object_or_404
from event.forms import EventForm
from event.models import Event, Registration

@login_required(login_url='/auth/login')
def show_event(request):
    events = Event.objects.all().order_by('date', 'start_time')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = serializers.serialize('json', events)
        return JsonResponse({'events': data})
    return render(request, 'show_event.html', {'events': events})

def show_event_json(request):
    user = request.user
    events = Event.objects.all().order_by('date', 'start_time')
    data = [
        {
            "id": event.id,
            "name": event.name,
            "description": event.description,
            "date": event.date.strftime('%Y-%m-%d'),
            "start_time": event.start_time.strftime('%H:%M'),
            "registered_count": event.registered_count,
            "venue_name": event.venue_name,
            "venue_address": event.venue_address,
            "venue_type": event.venue_type,
            "owner": event.owner.user.username,
            "owner_id": event.owner.user.id,
            "thumbnail": event.thumbnail or '',
            "is_owner": user.is_authenticated and event.owner == user.profile,
        }
        for event in events
    ]
    return JsonResponse(data, safe=False)

def show_event_json_by_id(request, id):
    event = get_object_or_404(Event, pk=id)
    user = request.user
    data = [
        {
            "id": event.id,
            "name": event.name,
            "description": event.description,
            "date": event.date.strftime('%Y-%m-%d'),
            "start_time": event.start_time.strftime('%H:%M'),
            "registered_count": event.registered_count,
            "venue_name": event.venue_name,
            "venue_address": event.venue_address,
            "venue_type": event.venue_type,
            "venue_id": event.venue.id,
            "owner": event.owner.user.username,
            "owner_id": event.owner.user.id,
            "thumbnail": event.thumbnail or '',
            "is_owner": user.is_authenticated and event.owner == user.profile,
        }
    ]
    return JsonResponse(data, safe=False)

@csrf_exempt
@login_required(login_url='/auth/login')
@require_http_methods(["POST"])
def create_event(request):
    form = EventForm(request.POST, user=request.user.profile)
    if form.is_valid():
        event = form.save(commit=False)
        event.owner = request.user.profile
        event.save()
        return JsonResponse({'message': 'Event berhasil dibuat!'}, status=201)
    return JsonResponse({'errors': form.errors}, status=400)

@login_required(login_url='/auth/login')
def show_event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = {
            'id': event.id,
            'name': event.name,
            'owner': event.owner.user.username,
            'owner_id': event.owner.user.id,
            'venue': event.venue_name,
            'venue_type': event.venue_type,
            'venue_address': event.venue_address,
            'date': event.date.strftime('%Y-%m-%d'),
            'start_time': event.start_time.strftime('%H:%M'),
            'description': event.description,
            'registered_count': event.registered_count,
            'thumbnail': event.thumbnail or '',
        }
        return JsonResponse({'event': data}, status=200)

    return render(request, 'event_detail.html', {'event': event})

@csrf_exempt
@login_required(login_url='/auth/login')
@require_http_methods(["PUT"])
def update_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    data = json.loads(request.body)

    if event.owner != request.user.profile:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    form = EventForm(data, instance=event, user=request.user.profile)
    if form.is_valid():
        form.save()
        return JsonResponse({'message': 'Event berhasil diperbarui!'})
    return JsonResponse({'errors': form.errors}, status=400)

@csrf_exempt
@login_required(login_url='/auth/login')
@require_http_methods(["DELETE"])
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if event.owner != request.user.profile:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    event.delete()
    return JsonResponse({'message': 'Event berhasil dihapus.'})

@csrf_exempt
@login_required(login_url='/auth/login')
@require_http_methods(["POST"])
def join_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    user = request.user
    try:
        if user.profile.role == 'OWNER':
            return JsonResponse({"message": "Owners cannot join events. Only users with 'User' role can join."}, status=400)
    except:
        pass

    if Registration.objects.filter(user=user, event=event).exists():
        return JsonResponse({"message": "You already registered for this event."}, status=400)

    Registration.objects.create(user=user, event=event)

    return JsonResponse({"message": "Successfully registered for the event!"}, status=200)


@login_required(login_url='/auth/login')
def check_registration(request, event_id):
    """Digunakan untuk memeriksa apakah user sudah terdaftar di event ini."""
    event = get_object_or_404(Event, id=event_id)
    user = request.user
    is_owner_role = False
    try:
        is_owner_role = user.profile.role == 'OWNER'
    except:
        is_owner_role = False
    is_registered = Registration.objects.filter(user=user, event=event).exists()
    
    return JsonResponse({
        "is_registered": is_registered,
        "is_owner": is_owner_role
    })