from django.shortcuts import get_object_or_404, render
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
        # Get the user's profile
        profile = request.user.profile
    except Profile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User profile not found.'}, status=403)

    # Get the venue object
    venue = get_object_or_404(Venue, pk=venue_id)

    # Prevent duplicate reviews by the same user for the same venue
    if Review.objects.filter(user=profile, venue=venue).exists():
        return JsonResponse({
            'status': 'error',
            'message': 'You have already submitted a review for this venue.'
        }, status=409)  # 409 Conflict

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
            # You can send back the new review data to update the UI dynamically
            'review': {
                'id': review.id,
                'rating': review.rating,
                'comment': review.comment,
                'user': review.user.user.username,
                'created_at': review.created_at.strftime('%B %d, %Y'),
                'last_modified': review.created_at.strftime('%B %d, %Y')
            }
        }, status=201)
    else:
        # Return form validation errors
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@login_required(login_url='/auth/login')
@require_http_methods(["POST"])  # Using POST as the HTML form method is POST
def edit_review(request, review_id):
    """
    Handles editing an existing review via AJAX POST request.
    The review_id comes from the URL.
    """
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User profile not found.'}, status=403)
        
    review = get_object_or_404(Review, pk=review_id)

    # Security Check: Ensure the user editing is the user who created it
    if review.user != profile:
        return JsonResponse({
            'status': 'error',
            'message': 'You do not have permission to edit this review.'
        }, status=403)  # 403 Forbidden

    form = ReviewForm(request.POST, instance=review)

    if form.is_valid():
        form.save()
        return JsonResponse({
            'status': 'success',
            'message': 'Review updated successfully.',
            'review': {
                'id': review.id,
                'rating': review.rating,
                'comment': review.comment
            }
        }, status=200)
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@login_required(login_url='/auth/login')
@require_http_methods(["DELETE"])
def delete_review(request, review_id):
    """
    Handles deleting an existing review via AJAX DELETE request.
    """
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User profile not found.'}, status=403)

    review = get_object_or_404(Review, pk=review_id)

    # Security Check: Ensure the user deleting is the user who created it
    if review.user != profile:
        return JsonResponse({
            'status': 'error',
            'message': 'You do not have permission to delete this review.'
        }, status=403)  # 403 Forbidden

    review.delete()
    return JsonResponse({
        'status': 'success',
        'message': 'Review deleted successfully.'
    }, status=200)

@require_http_methods(["GET"])
def get_reviews_json(request):
    """
    Returns JSON data for all reviews, optimized with select_related.
    Mirrors the get_venues_json pattern from the venue app.
    """
    # Optimized query to pre-fetch related user and venue details
    reviews = Review.objects.select_related('user__user', 'venue').all().order_by('-created_at')
    
    data = []
    for review in reviews:
        data.append({
            'id': review.id,
            'rating': review.rating,
            'comment': review.comment,
            'user': review.user.user.username,
            'user_profile_id': review.user.id,
            'venue_id': review.venue.id,
            'venue_name': review.venue.name,
            'created_at': review.created_at.strftime('%B %d, %Y'),
            'last_modified': review.last_modified.strftime('%B %d, %Y')
        })
        
    return JsonResponse(data, safe=False)

@require_http_methods(["GET"])
def get_review_json_by_id(request, review_id):
    """
    Returns JSON data for a single review by its ID.
    Mirrors the get_venue_json_by_id pattern from the venue app.
    """
    # Optimized query to pre-fetch related user and venue details
    review = get_object_or_404(
        Review.objects.select_related('user__user', 'venue'), 
        pk=review_id
    )
    
    data = {
        'id': review.id,
        'rating': review.rating,
        'comment': review.comment,
        'user': review.user.user.username,
        'user_profile_id': review.user.id,
        'venue_id': review.venue.id,
        'venue_name': review.venue.name,
        'created_at': review.created_at.strftime('%B %d, %Y'),
        'last_modified': review.last_modified.strftime('%B %d, %Y')
    }
    return JsonResponse(data)

def show_review_page(request):
    """
    A simple view that just renders the HTML page.
    The page itself will use JavaScript to fetch the review data.
    """
    # Assuming you named the file 'review_section.html'
    # and put it in 'review/templates/review/'
    # Adjust the path if you saved it elsewhere.
    return render(request, 'venue_reviews.html')