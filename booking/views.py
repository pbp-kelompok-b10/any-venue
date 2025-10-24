from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from venue.models import Venue
from .models import BookingSlot, Booking
import json
from datetime import datetime, timedelta

def cleanup_old_slots_and_create_new():
    """
    Delete slots older than today and create new slots for 7 days ahead if they don't exist
    """
    current_date = datetime.now().date()
    
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

@login_required
def booking_page(request, venue_id):
    # Clean up old slots and create new ones
    cleanup_old_slots_and_create_new()
    
    venue = get_object_or_404(Venue, id=venue_id)
    return render(request, "booking/booking_ajax.html", {"venue": venue})

@login_required
def get_slots(request, venue_id):
    date_str = request.GET.get("date")
    if not date_str:
        return JsonResponse([], safe=False)
    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    slots = BookingSlot.objects.filter(venue_id=venue_id, date=date).order_by("start_time")
    user_bookings = Booking.objects.filter(user=request.user.profile, slot__venue_id=venue_id, slot__date=date).values_list('slot_id', flat=True)
    
    # Get current date and time
    now = datetime.now()
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

