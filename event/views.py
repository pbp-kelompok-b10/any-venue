from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import datetime
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
from event.models import Event

 # @login_required
def show_event(request):
    events = Event.objects.all().order_by('date', 'start_time')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = serializers.serialize('json', events)
        return JsonResponse({'events': data})

    return render(request, 'show_event.html', {'events': events})

def show_event_json(request):
    events = Event.objects.all().order_by('date', 'start_time')
    data = [
        {
            "id": event.id,
            "name": event.name,
            "description": event.description,
            "date": event.date,
            "start_time": event.start_time,
            "total_slots": event.total_slots,
            "booked_slots": event.booked_slots,
            "available_slots": event.available_slots,
            "venue_name": event.venue_name,
            "venue_address": event.venue_address,
            "venue_type": event.venue_type,
            "owner": event.owner.username,
            "thumbnail": event.thumbnail,
        }
        for event in events
    ]
    return JsonResponse(data, safe=False)

def show_event_json_by_id(request, id):
    event = get_object_or_404(Event, pk=id)
    data = [
        {
            "id": event.id,
            "name": event.name,
            "description": event.description,
            "date": event.date,
            "start_time": event.start_time,
            "total_slots": event.total_slots,
            "booked_slots": event.booked_slots,
            "available_slots": event.available_slots,
            "venue_name": event.venue_name,
            "venue_address": event.venue_address,
            "venue_type": event.venue_type,
            "owner": event.owner.username,
            "thumbnail": event.thumbnail,
        }
    ]
    return JsonResponse(data, safe=False)

@csrf_exempt
 # @login_required
@require_http_methods(["POST"])
def create_event(request):
    form = EventForm(request.POST, user=request.user)
    if form.is_valid():
        event = form.save(commit=False)
        event.owner = request.user
        event.save()
        return JsonResponse({'message': 'Event berhasil dibuat!'}, status=201)
    return JsonResponse({'errors': form.errors}, status=400)

 # @login_required
def show_event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = {
            'id': event.id,
            'name': event.name,
            'owner': event.owner.username,
            'venue': event.venue_name,
            'venue_type': event.venue_type,
            'venue_address': event.venue_address,
            'date': event.date.strftime('%Y-%m-%d'),
            'start_time': event.start_time.strftime('%H:%M'),
            'description': event.description,
            'total_slots': event.total_slots,
            'booked_slots': event.booked_slots,
            'available_slots': event.available_slots,
            'thumbnail': event.thumbnail or '',
        }
        return JsonResponse({'event': data}, status=200)

    return render(request, 'event_detail.html', {'event': event})

@csrf_exempt
 # @login_required
@require_http_methods(["POST"])
def update_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    form = EventForm(request.POST, instance=event, user=request.user)
    if form.is_valid():
        form.save()
        return JsonResponse({'message': 'Event berhasil diperbarui!'})
    return JsonResponse({'errors': form.errors}, status=400)

@csrf_exempt
 # @login_required
@require_http_methods(["POST"])
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    return JsonResponse({'message': 'Event berhasil dihapus.'})