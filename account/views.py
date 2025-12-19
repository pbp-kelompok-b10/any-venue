from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from account.models import Profile
from booking.models import Booking
from review.models import Review
from venue.models import Venue
from event.models import Event
from django.views.decorators.csrf import csrf_exempt
import json
from authentication.views import logout
from django.views.decorators.http import require_GET, require_http_methods

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

    old_role = profile.role  # simpan role sebelum diubah

    username = data.get("username")
    if username:
        profile.user.username = username
        profile.user.save()

    role = data.get("role")
    if role and role in dict(Profile.ROLE_CHOICES).keys():
        profile.role = role
        profile.save()

        if role != old_role:
            #OWNER ke USER hapus venue miliknya
            if old_role == "OWNER" and role == "USER":
                deleted_venues = Venue.objects.filter(owner=request.user.profile)
                deleted_event = Event.objects.filter(owner=request.user.profile)
                count_venues = deleted_venues.count()
                count_event = deleted_event.count()
                deleted_venues.delete()
                deleted_event.delete()
                print(f"Hapus {count_venues} venue dan {count_event} Event milik {request.user.username}")

            #USER ke OWNER hapus review & booking miliknya
            elif old_role == "USER" and role == "OWNER":
                deleted_reviews = Review.objects.filter(user=request.user.profile)
                deleted_bookings = Booking.objects.filter(user=request.user.profile)
                count_reviews = deleted_reviews.count()
                count_bookings = deleted_bookings.count()
                deleted_reviews.delete()
                deleted_bookings.delete()
                print(f"Hapus {count_reviews} review dan {count_bookings} booking milik {request.user.username}")

    return JsonResponse({
        "success": True,
        "username": profile.user.username,
        "role": profile.get_role_display(),
    })

@login_required
@csrf_exempt  # karena pakai fetch
def delete_account(request):
    if request.method == "POST":
        try:
            user = request.user
            logout(request)  # logout dulu
            user.delete()    # hapus user
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request"})

@require_GET
@login_required
def get_profile_flutter(request):
    user = request.user  # user yang sedang login
    
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        return JsonResponse({"error": "Profile not found"}, status=404)

    data = {
        "username": user.username,
        "role": profile.role,
        "is_owner": profile.is_owner,
        "last_login": profile.last_login,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }

    return JsonResponse(data, status=200)



@require_http_methods(["POST"])
@login_required
def edit_profile_flutter(request):
    user = request.user
    
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        return JsonResponse({"error": "Profile not found"}, status=404)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    # Fields yang boleh di-update
    new_username = data.get("username")
    new_role = data.get("role")

    # Update user fields
    if new_username:
        user.username = new_username
    user.save()

    # Update profile fields
    if new_role:
        if new_role not in dict(Profile.ROLE_CHOICES):
            return JsonResponse({"error": "Invalid role"}, status=400)
        profile.role = new_role
        profile.save()

    return JsonResponse({
        "success": True,
        "message": "Profile updated successfully",
        "data": {
            "username": user.username,
            "role": profile.role,
            "is_owner": profile.is_owner,
            "last_login": profile.last_login,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
        }
    }, status=200)

@require_http_methods(["DELETE"])
@login_required
def delete_profile_flutter(request):
    user = request.user

    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        return JsonResponse({"error": "Profile not found"}, status=404)

    profile.delete()
    user.delete()

    return JsonResponse({
        "success": True,
        "message": "User and profile deleted successfully"
    }, status=200)

@require_GET
@login_required
def user_profile_api(request):
    # 1. Cek apakah user sudah login
    if not request.user.is_authenticated:
        return JsonResponse({
            "status": False,
            "message": "Anda belum login."
        }, status=401)

    try:
        # 2. Ambil objek Profile berdasarkan user yang sedang login
        # Sesuaikan 'user=request.user' dengan relasi OneToOne di model kamu
        profile = Profile.objects.get(user=request.user)

        # 3. Siapkan data dasar sesuai Model Dart Profile kamu
        # Pastikan field ini SAMA PERSIS dengan Profile.fromJson di Flutter
        user_data = {
            "username": request.user.username,
            "role": profile.role,
            "is_owner": profile.is_owner,
            # Gunakan .isoformat() agar DateTime bisa di-parse oleh Flutter
            "last_login": request.user.last_login.isoformat() if request.user.last_login else "",
            "created_at": profile.created_at.isoformat() if profile.created_at else "",
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else "",
        }

        # (Opsional) 4. Logika Tambahan untuk Owner vs User 
        # Jika kamu ingin mengirim data tambahan seperti list venue/booking di masa depan
        extra_data = {}
        if profile.is_owner:
            # venues = Venue.objects.filter(owner=profile)
            # extra_data['venues_count'] = venues.count()
            pass 
        else:
            # bookings = Booking.objects.filter(user=profile)
            # extra_data['bookings_count'] = bookings.count()
            pass

        # 5. Return JSON Response
        return JsonResponse({
            "status": True,
            "message": "Berhasil mengambil data profil",
            # Kita taruh data di key 'user_data' agar rapi, 
            # atau bisa langsung di root jika logic fluttermu mengharapkan itu.
            # Sesuai logika Login di diskusi sebelumnya, kita pakai struktur ini:
            "user_data": user_data, 
            
            # Opsional: Jika logic fluttermu langsung ambil dari root dictionary:
            **user_data 
        }, status=200)

    except Profile.DoesNotExist:
        return JsonResponse({
            "status": False,
            "message": "Profil pengguna tidak ditemukan."
        }, status=404)
    except Exception as e:
        return JsonResponse({
            "status": False,
            "message": f"Terjadi kesalahan: {str(e)}"
        }, status=500)