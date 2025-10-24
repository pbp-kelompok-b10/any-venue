from django.shortcuts import render

from review.models import Review
from venue.models import Venue

# Create your views here.
def show_landing(request):
    latest_venues = Venue.objects.order_by('-pk')[:3]
    latest_reviews = Review.objects.order_by('-created_at')[:3]
    context = {
        'venues_list': latest_venues,
        'reviews_list': latest_reviews,
    }

    return render(request, "landing.html", context)

def features_preview(request):
    return render(request, "sections/features_preview.html")

def header_test(request):
    return render(request, "sections/header.html")

def features_review(request):
    return render(request, "sections/features_review.html")

def booking_preview(request):
    return render(request, "sections/booking_preview.html")