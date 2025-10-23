import json
from datetime import date, time

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from .models import Court, BookingSlot, Booking


@login_required
def booking_ajax(request, court_id):
	court = get_object_or_404(Court, pk=court_id)
	return render(request, "booking/booking_ajax.html", {"court": court})


@login_required
def get_slots(request, court_id):
	selected_date = parse_date(request.GET.get("date")) or date.today()
	court = get_object_or_404(Court, pk=court_id)

	start_hour, end_hour = 8, 22
	existing_slots = BookingSlot.objects.filter(court=court, date=selected_date)
	if not existing_slots.exists():
		for h in range(start_hour, end_hour):
			BookingSlot.objects.create(
				court=court,
				date=selected_date,
				start_time=time(hour=h),
				end_time=time(hour=h + 1),
			)

	slots = BookingSlot.objects.filter(court=court, date=selected_date).order_by("start_time")
	data = [{
		"id": s.id,
		"start_time": s.start_time.strftime("%H:%M"),
		"end_time": s.end_time.strftime("%H:%M"),
		"is_booked": s.is_booked,
	} for s in slots]
	return JsonResponse({"slots": data})


@login_required
@require_POST
def make_booking(request, court_id):
	if hasattr(request.user, 'profile') and getattr(request.user.profile, 'role', None) == 'OWNER':
		return JsonResponse({"error": "Owner tidak bisa booking."}, status=403)

	try:
		payload = json.loads(request.body.decode("utf-8"))
	except Exception:
		payload = {}

	slot_ids = payload.get("slots", [])
	court = get_object_or_404(Court, pk=court_id)
	price_per_hour = getattr(court.venue, "price", 0)

	total_price = 0
	booked = []
	for sid in slot_ids:
		slot = BookingSlot.objects.filter(pk=sid, court=court, is_booked=False).first()
		if slot:
			slot.is_booked = True
			slot.save()
			Booking.objects.create(user=request.user, slot=slot, total_price=price_per_hour)
			total_price += price_per_hour
			booked.append(slot.id)

	return JsonResponse({
		"success": True,
		"total_price": total_price,
		"booked": booked,
		"redirect_url": f"/venue/detail/{court.venue.id}/"
	})


@login_required
@require_POST
def cancel_booking(request, court_id):
	try:
		payload = json.loads(request.body.decode("utf-8"))
	except Exception:
		payload = {}

	slot_ids = payload.get("slots", [])
	court = get_object_or_404(Court, pk=court_id)

	cancelled = []
	for sid in slot_ids:
		slot = BookingSlot.objects.filter(pk=sid, court=court).first()
		if slot:
			booking = Booking.objects.filter(user=request.user, slot=slot).first()
			if booking:
				booking.delete()
				slot.is_booked = False
				slot.save()
				cancelled.append(slot.id)

	return JsonResponse({"success": True, "cancelled": cancelled})