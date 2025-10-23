from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from account.models import Profile
from booking.models import Booking
from review.models import Review
from venue.models import Venue


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

    venues = Venue.objects.filter(owner=profile).values("id", "name", "city__name", "category__name", "price")
    return JsonResponse(list(venues), safe=False)


@login_required
def get_bookings_json(request):
    bookings = Booking.objects.filter(user=request.user).select_related("slot__venue")
    data = [
        {
            "id": b.id,
            "venue_name": b.slot.venue.name,
            "date": b.slot.date.strftime("%Y-%m-%d"),
            "status": "Booked",
        }
        for b in bookings
    ]
    return JsonResponse(data, safe=False)

@login_required
def get_reviews_json(request):
    profile = get_object_or_404(Profile, user=request.user)
    reviews = Review.objects.filter(user=profile).select_related("venue")
    data = [
        {
            "id": r.id,
            "venue_name": r.venue.name,
            "rating": r.rating,
            "comment": r.comment,
        }
        for r in reviews
    ]
    return JsonResponse(data, safe=False)
