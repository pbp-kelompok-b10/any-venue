from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from venue.models import Venue
from review.forms import ReviewForm
from review.models import Review
from account.models import Profile

@login_required(login_url='/auth/login')
@require_http_methods(["POST"])
def add_review(request, venue_id):
    """
    Handles adding a new review for a specific venue via AJAX POST request.
    """
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
                'created_at': review.created_at.strftime('%B %d, %Y %H:%M'),
                'last_modified': review.last_modified.strftime('%B %d, %Y %H:%M')
            }
        }, status=201)
    else:
        # Return form validation errors
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@login_required(login_url='/auth/login')
@require_http_methods(["POST"])  # Using POST as the HTML form method is POST
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
                'last_modified': review.last_modified.strftime('%B %d, %Y %H:%M')
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
    reviews = Review.objects.select_related('user__user', 'venue').all().order_by('-last_modified')
    
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
            'created_at': review.created_at.strftime('%B %d, %Y %H:%M'),
            'last_modified': review.last_modified.strftime('%B %d, %Y %H:%M')
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
        'created_at': review.created_at.strftime('%B %d, %Y %H:%M'),
        'last_modified': review.last_modified.strftime('%B %d, %Y %H:%M')
    }
    return JsonResponse(data)