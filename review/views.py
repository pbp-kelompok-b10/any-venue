import json
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import strip_tags
from django.http import JsonResponse
from venue.models import Venue
from review.forms import ReviewForm
from review.models import Review
from account.models import Profile

@login_required(login_url='/auth/login')
@require_http_methods(["POST"])
def add_review(request, venue_id):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User profile not found.'}, status=403)

    venue = get_object_or_404(Venue, pk=venue_id)

    # prevent duplicate reviews by the same user for the same venue
    if Review.objects.filter(user=profile, venue=venue).exists():
        return JsonResponse({
            'status': 'error',
            'message': 'You have already submitted a review for this venue.'
        }, status=409)

    form = ReviewForm(request.POST)

    if form.is_valid():
        review = form.save(commit=False)
        review.user = profile
        review.venue = venue
        review.save()
        
        # Return success response with created review data
        return JsonResponse({
            'status': 'success',
            'message': 'Review added successfully.',
            # send back the new review data to update the UI dynamically
            'review': {
                'id': review.id,
                'rating': review.rating,
                'comment': review.comment,
                'user': review.user.user.username,
                'created_at': review.created_at.strftime('%d-%m-%Y %H:%M'),
                'last_modified': review.last_modified.strftime('%d-%m-%Y %H:%M')
            }
        }, status=201)
    else:
        # Return form validation errors
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@login_required(login_url='/auth/login')
@require_http_methods(["POST"])
def edit_review(request, review_id):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User profile not found.'}, status=403)
        
    review = get_object_or_404(Review, pk=review_id)

    # Ensure the user editing is the user who created it
    if review.user != profile:
        return JsonResponse({
            'status': 'error',
            'message': 'You do not have permission to edit this review.'
        }, status=403)

    form = ReviewForm(request.POST, instance=review)

    if form.is_valid():
        review = form.save()
        return JsonResponse({
            'status': 'success',
            'message': 'Review updated successfully.',
            'review': {
                'id': review.id,
                'rating': review.rating,
                'comment': review.comment,
                'last_modified': review.last_modified.strftime('%d-%m-%Y %H:%M')
            }
        }, status=200)
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@login_required(login_url='/auth/login')
@require_http_methods(["DELETE"])
def delete_review(request, review_id):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User profile not found.'}, status=403)

    review = get_object_or_404(Review, pk=review_id)

    # Ensure the user deleting is the user who created it
    if review.user != profile:
        return JsonResponse({
            'status': 'error',
            'message': 'You do not have permission to delete this review.'
        }, status=403)

    review.delete()
    return JsonResponse({
        'status': 'success',
        'message': 'Review deleted successfully.'
    }, status=200)

@require_http_methods(["GET"])
def get_reviews_json(request):
    reviews = Review.objects.select_related('user__user', 'venue').all().order_by('-last_modified', '-pk')
    
    data = []
    for review in reviews:
        data.append({
            'id': review.id,
            'rating': review.rating,
            'comment': review.comment,
            'user': review.user.user.username,
            'user_profile_id': review.user.user.id,
            'venue_id': review.venue.id,
            'venue_name': review.venue.name,
            'created_at': review.created_at.strftime('%d-%m-%Y %H:%M'),
            'last_modified': review.last_modified.strftime('%d-%m-%Y %H:%M')
        })
        
    return JsonResponse(data, safe=False)

@require_http_methods(["GET"])
def get_review_json_by_id(request, review_id):
    review = get_object_or_404(
        Review.objects.select_related('user__user', 'venue'), 
        pk=review_id
    )
    
    data = {
        'id': review.id,
        'rating': review.rating,
        'comment': review.comment,
        'user': review.user.user.username,
        'user_profile_id': review.user.user.id,
        'venue_id': review.venue.id,
        'venue_name': review.venue.name,
        'created_at': review.created_at.strftime('%d-%m-%Y %H:%M'),
        'last_modified': review.last_modified.strftime('%d-%m-%Y %H:%M')
    }
    return JsonResponse(data)

@login_required(login_url='/auth/login')
@require_http_methods(["GET"])
def get_my_reviews_json(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return JsonResponse([], safe=False)

    reviews = Review.objects.filter(user=profile).select_related('user__user', 'venue').order_by('-last_modified', '-pk')
    
    data = []
    for review in reviews:
        data.append({
            'id': review.id,
            'rating': review.rating,
            'comment': review.comment,
            'user': review.user.user.username,
            'user_id': review.user.user.id,
            'venue_id': review.venue.id,
            'venue_name': review.venue.name,
            'created_at': review.created_at.strftime('%d-%m-%Y %H:%M'),
            'last_modified': review.last_modified.strftime('%d-%m-%Y %H:%M')
        })
        
    return JsonResponse(data, safe=False)

@require_http_methods(["GET"])
def get_json_by_venue(request, venue_id):
    reviews = Review.objects.filter(venue_id=venue_id).select_related('user__user', 'venue').order_by('-last_modified', '-pk')
    
    data = []
    for review in reviews:
        data.append({
            'id': review.id,
            'rating': review.rating,
            'comment': review.comment,
            'user': review.user.user.username,
            'user_id': review.user.user.id,
            'venue_id': review.venue.id,
            'venue_name': review.venue.name,
            'created_at': review.created_at.strftime('%d-%m-%Y %H:%M'),
            'last_modified': review.last_modified.strftime('%d-%m-%Y %H:%M')
        })
        
    return JsonResponse(data, safe=False)

@login_required(login_url='/auth/login')
@require_http_methods(["GET"])
def get_my_json_by_venue(request, venue_id):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return JsonResponse([], safe=False)

    reviews = Review.objects.filter(user=profile, venue_id=venue_id).select_related('user__user', 'venue')
    
    data = []
    for review in reviews:
        data.append({
            'id': review.id,
            'rating': review.rating,
            'comment': review.comment,
            'user': review.user.user.username,
            'user_id': review.user.user.id,
            'venue_id': review.venue.id,
            'venue_name': review.venue.name,
            'created_at': review.created_at.strftime('%d-%m-%Y %H:%M'),
            'last_modified': review.last_modified.strftime('%d-%m-%Y %H:%M')
        })
    
    return JsonResponse(data, safe=False)

@csrf_exempt
def add_review_flutter(request, venue_id):
    if request.method == 'POST':
        # 1. Validasi Autentikasi
        if not request.user.is_authenticated:
            return JsonResponse(
                {"status": "error", "message": "You must login first."},
                status=401,
            )

        # 2. Cek Profile User
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "User profile not found."},
                status=404,
            )

        # 3. Cek Venue
        venue = get_object_or_404(Venue, pk=venue_id)

        # 4. Cek Duplikasi Review (Satu user satu review per venue)
        if Review.objects.filter(user=profile, venue=venue).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'You have already submitted a review for this venue.'
            }, status=409)

        try:
            data = json.loads(request.body)
            
            # 5. Validasi Input
            rating = int(data.get("rating", 0))
            comment = strip_tags(data.get("comment", "")).strip()

            if not (1 <= rating <= 5):
                return JsonResponse({"status": "error", "message": "Rating must be between 1 and 5."}, status=400)

            # 6. Simpan Review
            new_review = Review(
                user=profile,
                venue=venue,
                rating=rating,
                comment=comment
            )
            new_review.save()

            return JsonResponse({
                "status": "success",
                "message": "Review added successfully.",
                "id": new_review.id,
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON body."}, status=400)
        except ValueError:
            return JsonResponse({"status": "error", "message": "Invalid data format."}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid method."}, status=405)


@csrf_exempt
def edit_review_flutter(request, review_id):
    if request.method == 'POST':
        # 1. Validasi Autentikasi
        if not request.user.is_authenticated:
            return JsonResponse(
                {"status": "error", "message": "You must login first."},
                status=401,
            )

        # 2. Ambil Review
        try:
            review = Review.objects.get(pk=review_id)
        except Review.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Review not found.'}, status=404)

        # 3. Validasi Kepemilikan
        # review.user adalah instance Profile, jadi kita bandingkan user dari profile tsb
        if review.user.user != request.user:
            return JsonResponse(
                {"status": "error", "message": "You are not allowed to edit this review."},
                status=403,
            )

        try:
            data = json.loads(request.body)

            # 4. Update data jika ada
            if "rating" in data:
                rating = int(data["rating"])
                if 1 <= rating <= 5:
                    review.rating = rating
                else:
                    return JsonResponse({"status": "error", "message": "Rating must be between 1 and 5."}, status=400)
            
            if "comment" in data:
                review.comment = strip_tags(data["comment"]).strip()

            review.save()

            return JsonResponse({
                "status": "success",
                "message": "Review updated successfully.",
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON body."}, status=400)
        except ValueError:
            return JsonResponse({"status": "error", "message": "Invalid data format."}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid method."}, status=405)


@csrf_exempt
def delete_review_flutter(request, review_id):
    if request.method == 'POST':
        # 1. Validasi Autentikasi
        if not request.user.is_authenticated:
            return JsonResponse(
                {"status": "error", "message": "You must login first."},
                status=401,
            )

        # 2. Ambil Review
        try:
            review = Review.objects.get(pk=review_id)
        except Review.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Review not found.'}, status=404)

        # 3. Validasi Kepemilikan
        if review.user.user != request.user:
            return JsonResponse(
                {"status": "error", "message": "You are not allowed to delete this review."},
                status=403,
            )

        # 4. Hapus Review
        review.delete()

        return JsonResponse({
            "status": "success",
            "message": "Review deleted successfully.",
        }, status=200)

    return JsonResponse({"status": "error", "message": "Invalid method."}, status=405)