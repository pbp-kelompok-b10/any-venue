from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .models import Venue, City, Category
from authentication.models import Profile

# Create your views here.
@login_required(login_url='/login')
def show_main(request): 
    try:
        user_profile = request.user.profile
    except Profile.DoesNotExist:
        return redirect('/register') 

    is_owner_role = user_profile.is_owner() if user_profile else False

    cities = City.objects.all().order_by('name')
    categories = Category.objects.all().order_by('name')
    types = Venue.TYPE_CHOICES

    context = {
        'profile': user_profile,
        'is_owner_role': is_owner_role,
        'user': request.user,
        'cities': cities,
        'categories': categories,
        'types': types,
    }

    return render(request, "venue_main.html", context)

def get_venues_json(request):
    venues = Venue.objects.select_related('owner__user', 'city', 'category').all()
    
    data = []
    for venue in venues:
        data.append({
            'id': str(venue.id), # Kirim UUID sebagai string
            'name': venue.name,
            'price': venue.price,
            'city_name': venue.city.name, # Kirim nama, bukan objek
            'category_name': venue.category.name, # Kirim nama, bukan objek
            'type': venue.type,
            'address': venue.address,
            'description': venue.description,
            'image_url': venue.image_url,
            'owner_profile_pk': venue.owner_id, 
            'owner_username': venue.owner.user.username,
        })
        
    return JsonResponse(data, safe=False)

def show_details(request, id):
    pass

def get_venue_json_by_id(request, venue_uuid):
    pass

def add_venue_ajax(request):
    pass

def edit_venue_ajax(request, venue_uuid):
    pass

def delete_venue_ajax(request, venue_uuid):
    pass