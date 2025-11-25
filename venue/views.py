import json, requests
from django.http import JsonResponse, HttpResponse
from django.utils.html import strip_tags
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, csrf_exempt
from .models import Venue, City, Category
from .forms import VenueForm
from account.models import Profile
from django.db.models import Avg, Count

# Create your views here.
@login_required(login_url='/auth/login')
def show_main(request): 
    """
    Menampilkan halaman utama (daftar venue).
    Halaman ini menangani pengecekan role pengguna (owner/user)
    dan memuat data untuk filter (kota, kategori, tipe).
    """
    try:
        user_profile = request.user.profile
    except Profile.DoesNotExist:
        return redirect('authentication:register') 

    is_owner_role = user_profile.is_owner if user_profile else False

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

@login_required(login_url='/auth/login')
def show_details(request, id):
    """
    Menampilkan halaman detail untuk satu venue spesifik berdasarkan ID.
    Juga menghitung dan menampilkan rata-rata rating dan jumlah review.
    """
    venue = get_object_or_404(Venue, pk=id)
    cities = City.objects.all().order_by('name')
    categories = Category.objects.all().order_by('name')
    review_agg = venue.reviews.aggregate(average_rating=Avg('rating'), review_count=Count('id')) 
    average_rating = review_agg['average_rating'] or 0 
    review_count = review_agg['review_count'] or 0

    context = {
        'venue': venue,
        'user': request.user,
        'cities': cities,
        'categories': categories,
        'average_rating': average_rating,
        'review_count': review_count,
    }
    return render(request, "venue_details.html", context)

@require_http_methods(["GET"])
def get_venues_json(request):
    """
    API endpoint (GET) untuk mengambil semua data venue dalam format JSON.
    Digunakan oleh AJAX/Fetch API di front-end untuk menampilkan daftar venue.
    """
    venues = Venue.objects.select_related('owner__user', 'city', 'category').all()
    
    data = []
    for venue in venues:
        data.append({
            'id': venue.id,
            'name': venue.name,
            'price': venue.price,
            'city_name': venue.city.name, # Kirim nama, bukan objek
            'category_name': venue.category.name, # Kirim nama, bukan objek
            'type': venue.type,
            'address': venue.address,
            'description': venue.description,
            'image_url': venue.image_url,
            'owner_profile_pk': str(venue.owner_id), # Kirim PK profile sbg string
            'owner_username': venue.owner.user.username,
        })
        
    return JsonResponse(data, safe=False)

@require_http_methods(["GET"])
def get_venue_json_by_id(request, id):
    """
    API endpoint (GET) untuk mengambil data satu venue spesifik berdasarkan ID.
    """
    venue = get_object_or_404(Venue, pk=id)
    
    data = {
        'id': venue.id,
        'name': venue.name,
        'price': venue.price,
        'type': venue.type,
        'city': venue.city.name, 
        'category': venue.category.name,
        'address': venue.address,
        'description': venue.description,
        'image_url': venue.image_url,
    }
    return JsonResponse(data)

@login_required(login_url='/auth/login')
@require_http_methods(["POST"])
def add_venue_ajax(request):
    """
    API endpoint (POST) untuk menambahkan venue baru .
    Hanya pengguna dengan role 'owner' yang bisa mengakses.
    """
    if not request.user.profile.is_owner:
        return JsonResponse({'error': 'You must be an owner to add a venue.'}, status=403)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    form = VenueForm(data)
    if form.is_valid():
        try:
            venue = form.save(commit=False) 
            venue.owner = request.user.profile 
            venue.save()
            return JsonResponse({'status': 'success', 'message': 'Venue berhasil ditambahkan'}, status=201)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        # Form tidak valid, kirim error validasi
        return JsonResponse(form.errors, status=400)

@login_required(login_url='/auth/login')
@require_http_methods(["PUT"])
def edit_venue_ajax(request, id):
    """
    API endpoint (PUT) untuk mengedit venue yang sudah ada.
    Hanya pemilik venue yang bisa mengedit.
    """
    try:
        venue = get_object_or_404(Venue, pk=id)
    except Venue.DoesNotExist:
         return JsonResponse({'error': 'Venue not found.'}, status=404)

    if venue.owner != request.user.profile:
        return JsonResponse({'error': 'You do not have permission to edit this venue.'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)
    
    form = VenueForm(data, instance=venue)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'success', 'id': venue.id}, status=200)
    else:
        # Form tidak valid, kirim error
        return JsonResponse(form.errors, status=400)

@login_required(login_url='/auth/login')
@require_http_methods(["DELETE"])
def delete_venue_ajax(request, id):
    """
    API endpoint (DELETE) untuk menghapus venue
    Hanya pemilik venue yang bisa menghapus.
    """
    try:
        venue = get_object_or_404(Venue, pk=id)
    except Venue.DoesNotExist:
         return JsonResponse({'error': 'Venue not found.'}, status=404)

    if venue.owner != request.user.profile:
        return JsonResponse({'error': 'You do not have permission to delete this venue.'}, status=403)

    venue.delete()
    return JsonResponse({'status': 'success', 'message': 'Venue deleted successfully.'}, status=200)

def proxy_image(request):
    image_url = request.GET.get('url')
    if not image_url:
        return HttpResponse('No URL provided', status=400)
    
    try:
        # Headers agar request tidak dianggap bot oleh server tujuan
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(image_url, headers=headers, timeout=10)
        
        # Return the image with proper content type
        return HttpResponse(
            response.content,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except requests.RequestException as e:
        return HttpResponse(f'Error fetching image: {str(e)}', status=500)

@require_http_methods(["GET"])
def get_venues_flutter(request):
    """
    API endpoint (GET) untuk mengambil semua data venue dalam format JSON.
    Mengirimkan data City, Category, dan Owner sebagai Objek (bukan String flat).
    """
    venues = Venue.objects.select_related('owner__user', 'city', 'category').all()
    
    data = []
    for venue in venues:
        data.append({
            'id': venue.id,
            'name': venue.name,
            'price': venue.price,
            'city': {
                'id': venue.city.id,
                'name': venue.city.name
            },
            'category': {
                'id': venue.category.id,
                'name': venue.category.name
            },
            'owner': {
                'id': venue.owner.pk, # ID Profile
                'username': venue.owner.user.username,
            },
            'type': venue.type,
            'address': venue.address,
            'description': venue.description,
            'image_url': venue.image_url,
        })
        
    return JsonResponse(data, safe=False)

@require_http_methods(["GET"])
def get_cities_flutter(request):
    """
    API endpoint (GET) untuk mengambil semua data city dalam format JSON.
    """
    cities = City.objects.all().order_by('name')
    data = [{'id': city.id, 'name': city.name} for city in cities]
    return JsonResponse(data, safe=False)

@require_http_methods(["GET"])
def get_categories_flutter(request):
    """
    API endpoint (GET) untuk mengambil semua data category dalam format JSON.
    """
    categories = Category.objects.all().order_by('name')
    data = [{'id': category.id, 'name': category.name} for category in categories]
    return JsonResponse(data, safe=False)
  
@csrf_exempt
def create_venue_flutter(request):
    if request.method == 'POST':
        # Validasi Autentikasi
        if not request.user.is_authenticated:
            return JsonResponse(
                {"status": "error", "message": "You must login first."},
                status=401,
            )

        # Cek apakah User memiliki Profile (dan Role Owner)
        try:
            profile = request.user.profile
            if not profile.is_owner:
                 return JsonResponse(
                    {"status": "error", "message": "Only owners can create venues."},
                    status=403,
                )
        except AttributeError:
             return JsonResponse(
                {"status": "error", "message": "User profile not found."},
                status=404,
            )

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON body."},
                status=400,
            )

        # Ambil dan bersihkan input
        name = strip_tags(data.get("name", "")).strip()
        price = data.get("price", 0)
        venue_type = strip_tags(data.get("type", "Indoor")).strip() # Default Indoor
        address = strip_tags(data.get("address", "")).strip()
        description = strip_tags(data.get("description", "")).strip()
        image_url = strip_tags(data.get("image_url", "")).strip()

        # Handle ForeignKey (City & Category)
        city_name = data.get("city", "")
        category_name = data.get("category", "")

        try:
            city_obj = City.objects.get(name=city_name)
        except City.DoesNotExist:
            return JsonResponse({"status": "error", "message": f"City '{city_name}' not found."}, status=404)

        try:
            category_obj = Category.objects.get(name=category_name)
        except Category.DoesNotExist:
            return JsonResponse({"status": "error", "message": f"Category '{category_name}' not found."}, status=404)

        # Buat Venue baru
        new_venue = Venue(
            owner=profile,
            name=name,
            price=price,
            city=city_obj,
            category=category_obj,
            type=venue_type,
            address=address,
            description=description,
            image_url=image_url
        )
        new_venue.save()

        return JsonResponse(
            {
                "status": "success",
                "message": "Venue created successfully.",
                "id": str(new_venue.id),
            },
            status=201,
        )

    return JsonResponse({"status": "error", "message": "Invalid method."}, status=405)


@csrf_exempt
def edit_venue_flutter(request, id):
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Invalid method."},
            status=405,
        )

    if not request.user.is_authenticated:
        return JsonResponse(
            {"status": "error", "message": "You must login first."},
            status=401,
        )

    venue = get_object_or_404(Venue, pk=id)

    # Validasi Kepemilikan (Hanya pemilik yang boleh edit)
    if venue.owner.user != request.user:
        return JsonResponse(
            {"status": "error", "message": "You are not allowed to edit this venue."},
            status=403,
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON body."},
            status=400,
        )

    # Update field jika ada datanya
    if "name" in data:
        venue.name = strip_tags(data["name"]).strip()
    if "price" in data:
        venue.price = int(data["price"])
    if "type" in data:
        venue.type = strip_tags(data["type"]).strip()
    if "address" in data:
        venue.address = strip_tags(data["address"]).strip()
    if "description" in data:
        venue.description = strip_tags(data["description"]).strip()
    if "image_url" in data:
        venue.image_url = strip_tags(data["image_url"]).strip()

    # Handle update ForeignKey (City & Category)
    if "city" in data:
        city_name = data["city"]
        try:
            venue.city = City.objects.get(name=city_name)
        except City.DoesNotExist:
             return JsonResponse({"status": "error", "message": f"City '{city_name}' not found."}, status=404)

    if "category" in data:
        category_name = data["category"]
        try:
            venue.category = Category.objects.get(name=category_name)
        except Category.DoesNotExist:
             return JsonResponse({"status": "error", "message": f"Category '{category_name}' not found."}, status=404)

    venue.save()

    return JsonResponse(
        {
            "status": "success",
            "message": "Venue updated successfully.",
        },
        status=200,
    )


@csrf_exempt
def delete_venue_flutter(request, id):
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Invalid method."},
            status=405,
        )

    if not request.user.is_authenticated:
        return JsonResponse(
            {"status": "error", "message": "You must login first."},
            status=401,
        )

    venue = get_object_or_404(Venue, pk=id)

    # Validasi Kepemilikan
    if venue.owner.user != request.user:
        return JsonResponse(
            {"status": "error", "message": "You are not allowed to delete this venue."},
            status=403,
        )

    venue.delete()

    return JsonResponse(
        {
            "status": "success",
            "message": "Venue deleted successfully.",
        },
        status=200,
    )