from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Profile#, Booking


def profile_page(request):
    if request.user.is_authenticated:
        profile = get_object_or_404(Profile, user=request.user)
        bookings = profile.bookings.all().order_by('-date')
    else:
        profile = None
        bookings = None
    return render(request, "profile_page.html", {"profile": profile, "bookings": bookings})


# def profile_page(request):
#     profile = get_object_or_404(Profile, user__username=request.user.username if request.user.is_authenticated else None)
#     # bookings = profile.bookings.all().order_by('-date') if request.user.is_authenticated else None
#     return render(request, "profile_page.html", {"profile": profile}) # "bookings": bookings

# @login_required
# def delete_booking(request):
#     if request.method == "POST":
#         booking_id = request.POST.get("id")
#         booking = get_object_or_404(Booking, id=booking_id, profile__user=request.user)
#         booking.delete()
#         return JsonResponse({"status": "ok"})
#     return JsonResponse({"status": "error"}, status=400)
