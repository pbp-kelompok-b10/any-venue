from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from account.models import Profile
from booking.models import Booking
from review.models import Review
from venue.models import Venue
from django.views.decorators.csrf import csrf_exempt
import json

def profile_page(request):
    if request.user.is_authenticated:
        profile = get_object_or_404(Profile, user=request.user)
        if profile.is_owner:
            venues = Venue.objects.filter(owner=profile)
            return render(request, "profile_page.html", {
                "profile": profile,
                "venues": venues
            })
        else:
            bookings = Booking.objects.filter(user=profile)
            reviews = Review.objects.filter(user=profile)
            return render(request, "profile_page.html", {
                "profile": profile,
                "bookings": bookings,
                "reviews": reviews
            })
    else:
        return render(request, "profile_page.html", {"profile": None})

@login_required
def get_venues_json(request):
    profile = get_object_or_404(Profile, user=request.user)
    if not profile.is_owner:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    venues = Venue.objects.filter(owner=profile).select_related("city", "category")
    
    data = [
        {
            "id": v.id,
            "name": v.name,
            "city": v.city.name if v.city else "Unknown City",
            "city_name": v.city.name if v.city else "Unknown City",  # untuk frontend
            "category": v.category.name if v.category else "Uncategorized",
            "category_name": v.category.name if v.category else "Uncategorized",  # untuk frontend
            "price": v.price,
            "type": v.type,
            "address": v.address,
            "description": v.description,
            "image_url": v.image_url,
            "owner_profile_pk": v.owner.pk
        }
        for v in venues
    ]
    
    return JsonResponse(data, safe=False)


@login_required
def get_bookings_json(request):
    try:
        profile = Profile.objects.get(user=request.user)
        bookings = Booking.objects.filter(user=profile).select_related("slot__venue")

        data = []
        for b in bookings:
            venue_name = b.slot.venue.name if b.slot and b.slot.venue else "Unknown Venue"
            date = b.slot.date.strftime("%Y-%m-%d") if b.slot else "Unknown Date"
            data.append({
                "id": b.id,
                "venue_name": venue_name,
                "date": date,
                "status": "Booked",
            })

        return JsonResponse(data, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def get_reviews_json(request):
    try:
        profile = Profile.objects.get(user=request.user)
        reviews = Review.objects.filter(user=profile).select_related("venue")

        data = []
        for r in reviews:
            venue_name = r.venue.name if r.venue else "Unknown Venue"
            data.append({
                "id": r.id,
                "venue_name": venue_name,
                "rating": r.rating,
                "comment": r.comment,
            })

        return JsonResponse(data, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)
   
@login_required
@csrf_exempt
def edit_profile(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        return JsonResponse({"error": "Profile not found"}, status=404)

    username = data.get("username")
    if username:
        profile.user.username = username
        profile.user.save()

    # optional: hanya allow role change untuk admin, jangan user biasa
    role = data.get("role")
    if role and role in dict(Profile.ROLE_CHOICES).keys():
        profile.role = role
        profile.save()

    return JsonResponse({
        "success": True,
        "username": profile.user.username,
        "role": profile.get_role_display(),
    })
