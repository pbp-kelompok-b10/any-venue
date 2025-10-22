from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .models import Venue, City, Category
from user.models import Profile

# Create your views here.
@login_required(login_url='/login')
def show_main(request): 
    filter_type = request.GET.get("filter", "all")  # default 'all'

    if filter_type == "all":
        products = Venue.objects.all()
    else:
        products = Venue.objects.filter(user=request.user)
        
    context = {
        'last_login': request.COOKIES.get('last_login', 'Never'),
        'user': request.user,
    }

    return render(request, "main.html", context)

def show_details(request):
    venue = get_object_or_404(Venue, id=65)
    context = {
        'venue': venue
    }
    return render(request, "venue_details.html", context)