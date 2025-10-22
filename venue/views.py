from django.shortcuts import get_object_or_404, render

from venue.models import Venue

# Create your views here.
def show_details(request):
    venue = get_object_or_404(Venue, id=65)
    context = {
        'venue': venue
    }
    return render(request, "venue_details.html", context)