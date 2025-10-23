from django.shortcuts import render, get_object_or_404
from account.models import Profile
from booking.models import Booking
from review.models import Review
from venue.models import Venue

def profile_page(request):
    if request.user.is_authenticated:
        profile = get_object_or_404(Profile, user=request.user)
        if profile.is_owner:
            venues = profile.venues.all()
            return render(request, "profile_page.html", {
                "profile": profile,
                "venues": venues
            })
        else:  # biasa user
            bookings = request.user.bookings.all()
            reviews = Review.objects.filter(user=profile)
            return render(request, "profile_page.html", {
                "profile": profile,
                "bookings": bookings,
                "reviews": reviews
            })
    else:
        # user belum login: coba ambil username terakhir login, atau profile kosong
        profile = None
        return render(request, "profile_page.html", {"profile": profile})
