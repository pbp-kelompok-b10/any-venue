from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from venue.models import Venue
from .models import BookingSlot, Booking
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.serializers import serialize

def cleanup_old_slots_and_create_new():
    """
    Delete slots older than today and create new slots for 7 days ahead if they don't exist
    """
    # Use timezone-aware current date
    current_date = timezone.localdate()
    
    # Delete old slots (older than today)
    old_slots = BookingSlot.objects.filter(date__lt=current_date)
    old_bookings_count = Booking.objects.filter(slot__date__lt=current_date).count()
    
    # Delete associated bookings first
    Booking.objects.filter(slot__date__lt=current_date).delete()
    old_slots.delete()
    
    # Create new slots for 7 days ahead for all venues
    venues = Venue.objects.all()
    for venue in venues:
        for day_offset in range(7):
            target_date = current_date + timedelta(days=day_offset)
            
            # Check if slots already exist for this date
            existing_slots = BookingSlot.objects.filter(venue=venue, date=target_date).exists()
            
            if not existing_slots:
                # Create slots from 8:00 to 22:00 (every hour)
                for hour in range(8, 22):
                    start_time = f"{hour:02d}:00:00"
                    end_time = f"{hour+1:02d}:00:00"
                    
                    BookingSlot.objects.create(
                        venue=venue,
                        date=target_date,
                        start_time=start_time,
                        end_time=end_time,
                        is_booked=False
                    )

def ensure_slots_for_date(venue, target_date, start_hour=8, end_hour=22):
    """
    Ensure hourly slots exist for a specific venue and date.
    Will create slots from start_hour to end_hour (exclusive) if none exist.
    Only creates for today or future dates to avoid resurrecting past days.
    """
    today = timezone.localdate()
    if target_date < today:
        return
    if not BookingSlot.objects.filter(venue=venue, date=target_date).exists():
        for hour in range(start_hour, end_hour):
            start_time = f"{hour:02d}:00:00"
            end_time = f"{hour+1:02d}:00:00"
            BookingSlot.objects.create(
                venue=venue,
                date=target_date,
                start_time=start_time,
                end_time=end_time,
                is_booked=False,
            )

def booking_page(request, venue_id):
    # Clean up old slots and create new ones
    cleanup_old_slots_and_create_new()
    
    venue = get_object_or_404(Venue, id=venue_id)
    return render(request, "booking/booking_ajax.html", {"venue": venue})

def get_slots(request, venue_id):
    date_str = request.GET.get("date")
    if not date_str:
        return JsonResponse([], safe=False)
    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    # Proactively create slots on-demand for future dates within horizon
    horizon_days = 30
    today = timezone.localdate()
    venue = get_object_or_404(Venue, id=venue_id)
    if today <= date <= today + timedelta(days=horizon_days):
        ensure_slots_for_date(venue, date)
    
    slots = BookingSlot.objects.filter(venue_id=venue_id, date=date).order_by("start_time")
    # Fallback: if still empty and within horizon, try once more (avoid racing reloads)
    if not slots.exists() and today <= date <= today + timedelta(days=horizon_days):
        ensure_slots_for_date(venue, date)
        slots = BookingSlot.objects.filter(venue_id=venue_id, date=date).order_by("start_time")
    # Determine user's existing bookings only if authenticated
    if request.user.is_authenticated:
        user_bookings = Booking.objects.filter(
            user=request.user.profile,
            slot__venue_id=venue_id,
            slot__date=date
        ).values_list('slot_id', flat=True)
    else:
        user_bookings = []
    
    # Get current date and time
    # Use timezone-aware current time
    now = timezone.localtime()
    current_date = now.date()
    current_time = now.time()
    
    # Filter out past slots and clean up past bookings
    available_slots = []
    for s in slots:
        # If the date is today, check if the slot time has passed
        if s.date == current_date and s.end_time < current_time:
            # Remove past bookings automatically
            if s.is_booked:
                Booking.objects.filter(slot=s).delete()
                s.is_booked = False
                s.save()
            continue  # Skip this slot, don't show it
        
        # If date is in the past, clean up and skip
        if s.date < current_date:
            if s.is_booked:
                Booking.objects.filter(slot=s).delete()
                s.is_booked = False
                s.save()
            continue
        
        # Add slot to available list
        available_slots.append({
            "id": s.id,
            "start_time": s.start_time.strftime("%H:%M"),
            "end_time": s.end_time.strftime("%H:%M"),
            "is_booked": s.is_booked,
            "is_booked_by_user": s.id in user_bookings,
            "price": s.venue.price,
        })
    
    return JsonResponse(available_slots, safe=False)

@csrf_exempt
@login_required
def create_booking(request):
    if request.method == "POST":
        payload = json.loads(request.body)
        slot_ids = payload.get("slots", [])
        user_profile = request.user.profile
        total = 0
        for sid in slot_ids:
            slot = get_object_or_404(BookingSlot, id=sid, is_booked=False)
            total += slot.venue.price
            slot.is_booked = True
            slot.save()
            Booking.objects.create(user=user_profile, slot=slot, total_price=slot.venue.price)
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
            booking = Booking.objects.get(user=request.user.profile, slot=slot)
            booking.delete()
            slot.is_booked = False
            slot.save()
            return JsonResponse({"status": "success"})
        except Booking.DoesNotExist:
            return JsonResponse({"status": "not_found"})
    return JsonResponse({"status": "error"})

def get_booking_json(request):
    bookings = Booking.objects.all()
    return JsonResponse(json.loads(serialize('json', bookings)), safe=False)

@login_required
def get_user_bookings_json(request):
    bookings = Booking.objects.filter(user=request.user.profile)
    return JsonResponse(json.loads(serialize('json', bookings)), safe=False)


@login_required
def get_user_bookings_upcoming(request):
    today = timezone.localdate()
    bookings = Booking.objects.filter(user=request.user.profile, slot__date__gte=today).order_by('slot__date', 'slot__start_time')
    return JsonResponse(json.loads(serialize('json', bookings)), safe=False)


@login_required
def get_user_bookings_past(request):
    today = timezone.localdate()
    bookings = Booking.objects.filter(user=request.user.profile, slot__date__lt=today).order_by('-slot__date', '-slot__start_time')
    return JsonResponse(json.loads(serialize('json', bookings)), safe=False)

@csrf_exempt
@login_required
def create_booking_flutter(request):
    if request.method == "POST":
        # Only allow USER role to book
        if getattr(request.user.profile, 'role', 'USER') != 'USER':
            return JsonResponse({"status": "error", "message": "Only USER role can book."}, status=403)

        payload = json.loads(request.body)
        slot_ids = payload.get("slots", [])
        user_profile = request.user.profile
        total = 0
        
        if not slot_ids:
            return JsonResponse({"status": "error", "message": "No slots provided."}, status=400)

        bookings_created = []
        for sid in slot_ids:
            try:
                slot = BookingSlot.objects.get(id=sid)
                if slot.is_booked:
                    return JsonResponse({"status": "error", "message": f"Slot {sid} is already booked."}, status=409)
                
                total += slot.venue.price
                slot.is_booked = True
                slot.save()
                
                new_booking = Booking.objects.create(user=user_profile, slot=slot, total_price=slot.venue.price)
                bookings_created.append(new_booking.id)

            except BookingSlot.DoesNotExist:
                return JsonResponse({"status": "error", "message": f"Slot {sid} not found."}, status=404)

        return JsonResponse({"status": "success", "total": total, "booking_ids": bookings_created}, status=201)
    
    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)

@csrf_exempt
@login_required
def cancel_booking_flutter(request):
    if request.method == "POST":
        if getattr(request.user.profile, 'role', 'USER') != 'USER':
            return JsonResponse({"status": "error", "message": "Only USER role can cancel."}, status=403)

        payload = json.loads(request.body)
        slot_id = payload.get("slot_id")

        if not slot_id:
            return JsonResponse({"status": "error", "message": "Slot ID not provided."}, status=400)

        try:
            slot = BookingSlot.objects.get(id=slot_id)
            booking = Booking.objects.get(user=request.user.profile, slot=slot)
            
            booking.delete()
            slot.is_booked = False
            slot.save()
            
            return JsonResponse({"status": "success", "message": "Booking canceled successfully."})
        
        except BookingSlot.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Slot not found."}, status=404)
        except Booking.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Booking not found for this user and slot."}, status=404)

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)


@login_required
def get_slot_venue_flutter(request, slot_id):
    """
    Return venue info for a given slot to let the mobile app deep-link back to the venue booking page.
    """
    try:
        slot = BookingSlot.objects.select_related('venue').get(id=slot_id)
        venue = slot.venue
        return JsonResponse(
            {
                "status": "success",
                "venue": {
                    "id": venue.id,
                    "name": venue.name,
                    "price": venue.price,
                    "address": venue.address,
                    "type": venue.type,
                    "image_url": venue.image_url,
                },
            }
        )
    except BookingSlot.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Slot not found."}, status=404)

