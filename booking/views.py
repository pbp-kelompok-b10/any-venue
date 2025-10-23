from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from venue.models import Venue
from .models import BookingSlot, Booking
import json
from datetime import datetime

@login_required
def booking_page(request, venue_id):
    venue = get_object_or_404(Venue, id=venue_id)
    return render(request, "booking/booking_ajax.html", {"venue": venue})

@login_required
def get_slots(request, venue_id):
    date_str = request.GET.get("date")
    if not date_str:
        return JsonResponse([], safe=False)
    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    slots = BookingSlot.objects.filter(venue_id=venue_id, date=date).order_by("start_time")
    return JsonResponse([
        {
            "id": s.id,
            "start_time": s.start_time.strftime("%H:%M"),
            "end_time": s.end_time.strftime("%H:%M"),
            "is_booked": s.is_booked,
            "price": s.venue.price,
        } for s in slots
    ], safe=False)

@csrf_exempt
@login_required
def create_booking(request):
    if request.method == "POST":
        payload = json.loads(request.body)
        slot_ids = payload.get("slots", [])
        user = request.user
        total = 0
        for sid in slot_ids:
            slot = get_object_or_404(BookingSlot, id=sid, is_booked=False)
            total += slot.venue.price
            slot.is_booked = True
            slot.save()
            Booking.objects.create(user=user, slot=slot, total_price=slot.venue.price_per_hour)
        return JsonResponse({"status": "success", "total": total})
    return JsonResponse({"status": "error"})

@csrf_exempt
@login_required
def cancel_booking(request):
    if request.method == "POST":
        payload = json.loads(request.body)
        slot_id = payload.get("slot_id")
        try:
            slot = BookingSlot.objects.get(id=slot_id)
            booking = Booking.objects.get(user=request.user, slot=slot)
            booking.delete()
            slot.is_booked = False
            slot.save()
            return JsonResponse({"status": "success"})
        except Booking.DoesNotExist:
            return JsonResponse({"status": "not_found"})
    return JsonResponse({"status": "error"})

