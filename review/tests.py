import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

# import from other apps
from account.models import Profile
from venue.models import Venue, City, Category 

# import from review
from .models import Review
from .forms import ReviewForm

class ReviewTest(TestCase):

    def setUp(self):
        # 3 users (1 venue owner, 2 regular users)
        # profiles for each user
        # 1 city and 1 category for venue
        # 1 venue owned by the owner
        # 1 review from user1
        
        self.owner_user = User.objects.create_user(username='venueowner', password='password123')
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        
        self.owner_profile = Profile.objects.get(user=self.owner_user)
        self.profile1 = Profile.objects.get(user=self.user1)
        self.profile2 = Profile.objects.get(user=self.user2)
        
        self.city = City.objects.create(name='Test City')
        self.category = Category.objects.create(name='Test Category')
        
        self.venue = Venue.objects.create(
            owner=self.owner_profile,
            name='Test Venue',
            price=100000,
            city=self.city,
            category=self.category,
            type='Indoor',
            address='Jl. Test No. 1'
        )
        
        self.review1 = Review.objects.create(
            user=self.profile1,
            venue=self.venue,
            rating=5,
            comment="This place is great!"
        )
        
        # initialize the test client
        self.client = Client()

        # define urls
        self.add_url = reverse('review:add_review', args=[self.venue.id])
        self.edit_url = reverse('review:edit_review', args=[self.review1.id])
        self.delete_url = reverse('review:delete_review', args=[self.review1.id])
        self.get_all_url = reverse('review:get_reviews_json')
        self.get_by_id_url = reverse('review:get_review_json_by_id', args=[self.review1.id])

    # model tests
    
    def test_review_model_creation(self):
        self.assertEqual(self.review1.user, self.profile1)
        self.assertEqual(self.review1.venue, self.venue)
        self.assertEqual(self.review1.rating, 5)
        self.assertEqual(self.review1.comment, "This place is great!")
        self.assertEqual(Review.objects.count(), 1)

    def test_review_model_str(self):
        expected_str = f'{self.user1.username} - {self.venue.name} ({self.review1.rating}/5)'
        self.assertEqual(str(self.review1), expected_str)

    # form tests

    def test_review_form_valid(self):
        data = {'rating': 4, 'comment': 'It was pretty good.'}
        form = ReviewForm(data=data)
        self.assertTrue(form.is_valid())

    def test_review_form_invalid_missing_rating(self):
        data = {'comment': 'I forgot to add a rating.'}
        form = ReviewForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)

    def test_review_form_valid_blank_comment(self):
        data = {'rating': 3}
        form = ReviewForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['comment'], '')

    # view: add_review tests

    def test_add_review_success(self):
        self.client.login(username='user2', password='password123')
        review_count_before = Review.objects.count()
        
        data = {'rating': 4, 'comment': 'A new review from user2.'}
        response = self.client.post(self.add_url, data)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Review.objects.count(), review_count_before + 1)
        
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['review']['comment'], 'A new review from user2.')
        self.assertEqual(data['review']['user'], self.user2.username)

    def test_add_review_not_logged_in(self):
        data = {'rating': 4, 'comment': 'I am not logged in.'}
        response = self.client.post(self.add_url, data)
        self.assertRedirects(response, '/auth/login?next=' + self.add_url, fetch_redirect_response=False)

    def test_add_review_duplicate(self):
        self.client.login(username='user1', password='password123') # user1 already reviewed
        review_count_before = Review.objects.count()

        data = {'rating': 1, 'comment': 'My second review.'}
        response = self.client.post(self.add_url, data)
        
        self.assertEqual(response.status_code, 409) # 409 Conflict
        self.assertEqual(Review.objects.count(), review_count_before)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertIn('You have already submitted', data['message'])

    def test_add_review_invalid_form(self):
        self.client.login(username='user2', password='password123')
        data = {'comment': 'This review has no rating.'} # Missing 'rating'
        response = self.client.post(self.add_url, data)
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertIn('rating', data['errors'])

    def test_add_review_nonexistent_venue(self):
        self.client.login(username='user2', password='password123')
        bad_url = reverse('review:add_review', args=[999])
        data = {'rating': 5, 'comment': 'For a venue that does not exist.'}
        response = self.client.post(bad_url, data)
        self.assertEqual(response.status_code, 404)

    # view: edit_review tests

    def test_edit_review_success(self):
        self.client.login(username='user1', password='password123')
        
        edit_data = {'rating': 1, 'comment': 'This is an edited comment.'}
        response = self.client.post(self.edit_url, edit_data)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['review']['comment'], 'This is an edited comment.')
        self.assertEqual(data['review']['rating'], 1)
        
        self.review1.refresh_from_db()
        self.assertEqual(self.review1.comment, 'This is an edited comment.')
        self.assertEqual(self.review1.rating, 1)

    def test_edit_review_not_owner(self):
        self.client.login(username='user2', password='password123') # Logged in as user2
        
        edit_data = {'rating': 2, 'comment': 'I am user2 trying to edit.'}
        response = self.client.post(self.edit_url, edit_data) # Attacking review1
        
        self.assertEqual(response.status_code, 403) # 403 Forbidden
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertIn('You do not have permission', data['message'])

    def test_edit_review_not_logged_in(self):
        edit_data = {'rating': 2, 'comment': 'Trying to edit while logged out.'}
        response = self.client.post(self.edit_url, edit_data)
        self.assertRedirects(response, '/auth/login?next=' + self.edit_url, fetch_redirect_response=False)

    def test_edit_review_method_not_allowed(self):
        self.client.login(username='user1', password='password123')
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 405) # 405 Method Not Allowed

    # view: delete_review tests

    def test_delete_review_success(self):
        self.client.login(username='user1', password='password123')
        review_count_before = Review.objects.count()

        response = self.client.delete(self.delete_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Review.objects.count(), review_count_before - 1)
        
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        
        with self.assertRaises(Review.DoesNotExist):
            Review.objects.get(id=self.review1.id)

    def test_delete_review_not_owner(self):
        self.client.login(username='user2', password='password123') # Logged in as user2
        review_count_before = Review.objects.count()

        response = self.client.delete(self.delete_url) # Attacking review1
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Review.objects.count(), review_count_before)
        data = json.loads(response.content)
        self.assertIn('You do not have permission', data['message'])

    def test_delete_review_not_logged_in(self):
        response = self.client.delete(self.delete_url)
        self.assertRedirects(response, '/auth/login?next=' + self.delete_url, fetch_redirect_response=False)

    def test_delete_review_method_not_allowed(self):
        self.client.login(username='user1', password='password123')
        response_post = self.client.post(self.delete_url)
        self.assertEqual(response_post.status_code, 405)
        response_get = self.client.get(self.delete_url)
        self.assertEqual(response_get.status_code, 405)

    # view: get_reviews_json tests

    def test_get_reviews_json_success(self):
        # create a second review to get a list
        Review.objects.create(
            user=self.profile2,
            venue=self.venue,
            rating=1,
            comment="Bad place!"
        )
        
        response = self.client.get(self.get_all_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        
        # newest first
        self.assertEqual(data[0]['user'], self.profile2.user.username)
        self.assertEqual(data[1]['user'], self.profile1.user.username)

    # view: get_review_json_by_id tests
    
    def test_get_review_json_by_id_success(self):
        response = self.client.get(self.get_by_id_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        self.assertIsInstance(data, dict)
        self.assertEqual(data['id'], self.review1.id)
        self.assertEqual(data['user'], self.user1.username)
        self.assertEqual(data['comment'], self.review1.comment)
        
    def test_get_review_json_by_id_not_found(self):
        bad_url = reverse('review:get_review_json_by_id', args=[999])
        response = self.client.get(bad_url)
        self.assertEqual(response.status_code, 404)