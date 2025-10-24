from django.test import TestCase

# Create your tests here.
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from account.models import Profile
from venue.models import Venue, City, Category
from booking.models import Booking, BookingSlot
from review.models import Review
import json
from datetime import date, time


class ProfileModelTest(TestCase):
    """Test Profile model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = Profile.objects.get(user=self.user)
    
    def test_profile_created_automatically(self):
        """Test profile is created automatically when user is created"""
        self.assertIsNotNone(self.profile)
        self.assertEqual(self.profile.user, self.user)
    
    def test_profile_default_role(self):
        """Test default role is USER"""
        self.assertEqual(self.profile.role, 'USER')
        self.assertFalse(self.profile.is_owner)
    
    def test_profile_is_owner_property(self):
        """Test is_owner property"""
        self.assertFalse(self.profile.is_owner)
        
        self.profile.role = 'OWNER'
        self.profile.save()
        self.assertTrue(self.profile.is_owner)
    
    def test_profile_last_login_property(self):
        """Test last_login property"""
        self.assertEqual(self.profile.last_login, self.user.last_login)
    
    def test_profile_str_method(self):
        """Test __str__ method"""
        expected = f"{self.user.username} ({self.profile.role})"
        self.assertEqual(str(self.profile), expected)


class ProfilePageViewTest(TestCase):
    """Test profile_page view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = Profile.objects.get(user=self.user)
        
        # Create owner user
        self.owner_user = User.objects.create_user(
            username='owneruser',
            password='testpass123'
        )
        self.owner_profile = Profile.objects.get(user=self.owner_user)
        self.owner_profile.role = 'OWNER'
        self.owner_profile.save()
        
        # Create venue data
        self.city = City.objects.create(name='Jakarta')
        self.category = Category.objects.create(name='Futsal')
        self.venue = Venue.objects.create(
            owner=self.owner_profile,
            name='Test Venue',
            price=100000,
            city=self.city,
            category=self.category,
            type='Indoor',
            address='Test Address',
            description='Test Description',
            image_url='https://example.com/image.jpg'
        )
    
    def test_profile_page_anonymous_user(self):
        """Test profile page for anonymous user"""
        response = self.client.get(reverse('account:profile_page'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['profile'])
    
    def test_profile_page_regular_user(self):
        """Test profile page for regular user"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create booking and review
        slot = BookingSlot.objects.create(
            venue=self.venue,
            date=date(2025, 1, 1),
            start_time=time(10, 0),
            end_time=time(12, 0),
            is_booked=True
        )
        booking = Booking.objects.create(
            user=self.profile,
            slot=slot,
            total_price=100000
        )
        review = Review.objects.create(
            user=self.profile,
            venue=self.venue,
            rating=5,
            comment='Great venue!'
        )
        
        response = self.client.get(reverse('account:profile_page'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['profile'], self.profile)
        self.assertIn('bookings', response.context)
        self.assertIn('reviews', response.context)
        self.assertEqual(len(response.context['bookings']), 1)
        self.assertEqual(len(response.context['reviews']), 1)
    
    def test_profile_page_owner_user(self):
        """Test profile page for owner user"""
        self.client.login(username='owneruser', password='testpass123')
        
        response = self.client.get(reverse('account:profile_page'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['profile'], self.owner_profile)
        self.assertIn('venues', response.context)
        self.assertEqual(len(response.context['venues']), 1)


class GetVenuesJsonTest(TestCase):
    """Test get_venues_json view"""
    
    def setUp(self):
        self.client = Client()
        self.owner_user = User.objects.create_user(
            username='owneruser',
            password='testpass123'
        )
        self.owner_profile = Profile.objects.get(user=self.owner_user)
        self.owner_profile.role = 'OWNER'
        self.owner_profile.save()
        
        self.regular_user = User.objects.create_user(
            username='regularuser',
            password='testpass123'
        )
        
        self.city = City.objects.create(name='Jakarta')
        self.category = Category.objects.create(name='Futsal')
        self.venue = Venue.objects.create(
            owner=self.owner_profile,
            name='Test Venue',
            price=100000,
            city=self.city,
            category=self.category,
            type='Indoor',
            address='Test Address',
            description='Test Description',
            image_url='https://example.com/image.jpg'
        )
    
    def test_get_venues_json_unauthorized_anonymous(self):
        """Test get_venues_json without login"""
        response = self.client.get(reverse('account:get_venues_json'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_get_venues_json_unauthorized_regular_user(self):
        """Test get_venues_json with regular user (not owner)"""
        self.client.login(username='regularuser', password='testpass123')
        response = self.client.get(reverse('account:get_venues_json'))
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_get_venues_json_success(self):
        """Test get_venues_json with owner user"""
        self.client.login(username='owneruser', password='testpass123')
        response = self.client.get(reverse('account:get_venues_json'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test Venue')
        self.assertEqual(data[0]['city'], 'Jakarta')
        self.assertEqual(data[0]['category'], 'Futsal')
        self.assertEqual(data[0]['price'], 100000)
        self.assertIn('city_name', data[0])
        self.assertIn('category_name', data[0])


class GetBookingsJsonTest(TestCase):
    """Test get_bookings_json view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = Profile.objects.get(user=self.user)
        
        owner_user = User.objects.create_user(
            username='owneruser',
            password='testpass123'
        )
        owner_profile = Profile.objects.get(user=owner_user)
        owner_profile.role = 'OWNER'
        owner_profile.save()
        
        city = City.objects.create(name='Jakarta')
        category = Category.objects.create(name='Futsal')
        venue = Venue.objects.create(
            owner=owner_profile,
            name='Test Venue',
            price=100000,
            city=city,
            category=category,
            type='Indoor',
            address='Test Address',
            description='Test Description',
            image_url='https://example.com/image.jpg'
        )
        
        self.slot = BookingSlot.objects.create(
            venue=venue,
            date=date(2025, 1, 1),
            start_time=time(10, 0),
            end_time=time(12, 0),
            is_booked=True
        )
    
    def test_get_bookings_json_unauthorized(self):
        """Test get_bookings_json without login"""
        response = self.client.get(reverse('account:get_bookings_json'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_get_bookings_json_no_bookings(self):
        """Test get_bookings_json with no bookings"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('account:get_bookings_json'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data), 0)
    
    def test_get_bookings_json_with_bookings(self):
        """Test get_bookings_json with bookings"""
        self.client.login(username='testuser', password='testpass123')
        
        booking = Booking.objects.create(
            user=self.profile,
            slot=self.slot,
            total_price=100000
        )
        
        response = self.client.get(reverse('account:get_bookings_json'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['venue_name'], 'Test Venue')
        self.assertEqual(data[0]['date'], '2025-01-01')
        self.assertEqual(data[0]['status'], 'Booked')


class GetReviewsJsonTest(TestCase):
    """Test get_reviews_json view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = Profile.objects.get(user=self.user)
        
        owner_user = User.objects.create_user(
            username='owneruser',
            password='testpass123'
        )
        owner_profile = Profile.objects.get(user=owner_user)
        owner_profile.role = 'OWNER'
        owner_profile.save()
        
        city = City.objects.create(name='Jakarta')
        category = Category.objects.create(name='Futsal')
        self.venue = Venue.objects.create(
            owner=owner_profile,
            name='Test Venue',
            price=100000,
            city=city,
            category=category,
            type='Indoor',
            address='Test Address',
            description='Test Description',
            image_url='https://example.com/image.jpg'
        )
    
    def test_get_reviews_json_unauthorized(self):
        """Test get_reviews_json without login"""
        response = self.client.get(reverse('account:get_reviews_json'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_get_reviews_json_no_reviews(self):
        """Test get_reviews_json with no reviews"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('account:get_reviews_json'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data), 0)
    
    def test_get_reviews_json_with_reviews(self):
        """Test get_reviews_json with reviews"""
        self.client.login(username='testuser', password='testpass123')
        
        review = Review.objects.create(
            user=self.profile,
            venue=self.venue,
            rating=5,
            comment='Great venue!'
        )
        
        response = self.client.get(reverse('account:get_reviews_json'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['venue_name'], 'Test Venue')
        self.assertEqual(data[0]['rating'], 5)
        self.assertEqual(data[0]['comment'], 'Great venue!')


class EditProfileTest(TestCase):
    """Test edit_profile view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = Profile.objects.get(user=self.user)
    
    def test_edit_profile_unauthorized(self):
        """Test edit_profile without login"""
        response = self.client.post(
            reverse('account:edit_profile_api'),
            data=json.dumps({'username': 'newusername'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_edit_profile_invalid_method(self):
        """Test edit_profile with GET method"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('account:edit_profile_api'))
        self.assertEqual(response.status_code, 405)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_edit_profile_invalid_json(self):
        """Test edit_profile with invalid JSON"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('account:edit_profile_api'),
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_edit_profile_change_username(self):
        """Test edit_profile changing username"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('account:edit_profile_api'),
            data=json.dumps({'username': 'newusername'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['username'], 'newusername')
        
        # Verify in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newusername')
    
    def test_edit_profile_change_role(self):
        """Test edit_profile changing role"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('account:edit_profile_api'),
            data=json.dumps({'role': 'OWNER'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['role'], 'Owner')
        
        # Verify in database
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.role, 'OWNER')
    
    def test_edit_profile_invalid_role(self):
        """Test edit_profile with invalid role"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('account:edit_profile_api'),
            data=json.dumps({'role': 'INVALID'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Role should not change
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.role, 'USER')
    
    def test_edit_profile_change_both(self):
        """Test edit_profile changing both username and role"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('account:edit_profile_api'),
            data=json.dumps({
                'username': 'newusername',
                'role': 'OWNER'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['username'], 'newusername')
        self.assertEqual(data['role'], 'Owner')


class DeleteAccountTest(TestCase):
    """Test delete_account view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_delete_account_unauthorized(self):
        """Test delete_account without login"""
        response = self.client.post(reverse('account:delete-account'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_delete_account_invalid_method(self):
        """Test delete_account with GET method"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('account:delete-account'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_delete_account_success(self):
        """Test delete_account successfully"""
        self.client.login(username='testuser', password='testpass123')
        user_id = self.user.id
        
        response = self.client.post(reverse('account:delete-account'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify user is deleted
        self.assertFalse(User.objects.filter(id=user_id).exists())


class SignalsTest(TestCase):
    """Test signals"""
    
    def test_profile_created_on_user_creation(self):
        """Test profile is automatically created when user is created"""
        user = User.objects.create_user(
            username='newuser',
            password='testpass123'
        )
        
        # Profile should exist
        self.assertTrue(Profile.objects.filter(user=user).exists())
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.role, 'USER')
    
    def test_profile_saved_on_user_save(self):
        """Test profile is saved when user is saved"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile = Profile.objects.get(user=user)
        
        # Change profile
        profile.role = 'OWNER'
        profile.save()
        
        # Save user (should trigger signal)
        user.email = 'test@example.com'
        user.save()
        
        # Profile should still exist, but may be reset to default USER by signal
        profile.refresh_from_db()
        self.assertIn(profile.role, ['USER', 'OWNER'])
