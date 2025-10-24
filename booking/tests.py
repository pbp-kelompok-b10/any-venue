from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, time, timedelta
from account.models import Profile
from venue.models import Venue, City, Category
from .models import BookingSlot, Booking
import json

class BookingModelTest(TestCase):
    def setUp(self):
        # Create user and profile (owner)
        self.owner_user = User.objects.create_user(username='owner', password='testpass123')
        self.owner_profile = Profile.objects.get(user=self.owner_user)
        self.owner_profile.role = 'OWNER'
        self.owner_profile.save()
        
        # Create user and profile (customer)
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.profile = Profile.objects.get(user=self.user)
        
        # Create city and category
        self.city = City.objects.create(name='Test City')
        self.category = Category.objects.create(name='Test Category')
        
        # Create venue
        self.venue = Venue.objects.create(
            owner=self.owner_profile,
            name='Test Venue',
            address='Test Address',
            type='Indoor',
            price=100000,
            city=self.city,
            category=self.category,
            description='Test description',
            image_url='https://example.com/image.jpg'
        )
        
        # Create booking slot
        self.slot = BookingSlot.objects.create(
            venue=self.venue,
            date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            is_booked=False
        )
    
    def test_booking_slot_creation(self):
        """Test booking slot is created correctly"""
        self.assertEqual(self.slot.venue, self.venue)
        self.assertFalse(self.slot.is_booked)
        self.assertEqual(str(self.slot), f"{self.venue.name} | {self.slot.date} | {self.slot.start_time}-{self.slot.end_time}")
    
    def test_booking_creation(self):
        """Test booking is created correctly"""
        booking = Booking.objects.create(
            user=self.profile,
            slot=self.slot,
            total_price=100000
        )
        self.assertEqual(booking.user, self.profile)
        self.assertEqual(booking.slot, self.slot)
        self.assertEqual(booking.total_price, 100000)

class BookingViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create owner user and profile
        self.owner_user = User.objects.create_user(username='owner', password='testpass123')
        self.owner_profile = Profile.objects.get(user=self.owner_user)
        self.owner_profile.role = 'OWNER'
        self.owner_profile.save()
        
        # Create user and profile (customer)
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.profile = Profile.objects.get(user=self.user)
        
        # Create city and category
        self.city = City.objects.create(name='Test City')
        self.category = Category.objects.create(name='Test Category')
        
        # Create venue
        self.venue = Venue.objects.create(
            owner=self.owner_profile,
            name='Test Venue',
            address='Test Address',
            type='Indoor',
            price=100000,
            city=self.city,
            category=self.category,
            description='Test description',
            image_url='https://example.com/image.jpg'
        )
        
        # Create booking slot
        self.slot = BookingSlot.objects.create(
            venue=self.venue,
            date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            is_booked=False
        )
    
    def test_booking_page_public_access(self):
        """Booking page should be accessible without login"""
        response = self.client.get(reverse('booking:booking_page', args=[self.venue.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.venue.name)
    
    def test_booking_page_authenticated(self):
        """Test booking page loads for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('booking:booking_page', args=[self.venue.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.venue.name)
    
    def test_get_slots_public(self):
        """Getting available slots should work without login"""
        tomorrow = date.today() + timedelta(days=1)
        response = self.client.get(
            reverse('booking:get_slots', args=[self.venue.id]),
            {'date': tomorrow.strftime('%Y-%m-%d')}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)

    def test_create_booking_requires_login(self):
        """Creating booking without login should redirect"""
        response = self.client.post(
            reverse('booking:create_booking'),
            json.dumps({'slots': [self.slot.id]}),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [302, 401])

    def test_cancel_booking_requires_login(self):
        """Cancel booking without login should redirect"""
        response = self.client.post(
            reverse('booking:cancel_booking'),
            json.dumps({'slot_id': self.slot.id}),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [302, 401])
    
    def test_create_booking(self):
        """Test creating a booking"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('booking:create_booking'),
            json.dumps({'slots': [self.slot.id]}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        
        # Check slot is now booked
        self.slot.refresh_from_db()
        self.assertTrue(self.slot.is_booked)
        
        # Check booking was created
        self.assertTrue(Booking.objects.filter(user=self.profile, slot=self.slot).exists())
    
    def test_cancel_booking(self):
        """Test canceling a booking"""
        # Create a booking first
        booking = Booking.objects.create(
            user=self.profile,
            slot=self.slot,
            total_price=100000
        )
        self.slot.is_booked = True
        self.slot.save()
        
        # Cancel the booking
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('booking:cancel_booking'),
            json.dumps({'slot_id': self.slot.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        
        # Check slot is available again
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_booked)
        
        # Check booking was deleted
        self.assertFalse(Booking.objects.filter(id=booking.id).exists())
    
    def test_cannot_book_already_booked_slot(self):
        """Test cannot book a slot that is already booked"""
        self.slot.is_booked = True
        self.slot.save()
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('booking:create_booking'),
            json.dumps({'slots': [self.slot.id]}),
            content_type='application/json'
        )
        
        # Should return error because slot is already booked
        self.assertEqual(response.status_code, 404)

class BookingCleanupTest(TestCase):
    def setUp(self):
        # Create owner user and profile
        self.owner_user = User.objects.create_user(username='owner', password='testpass123')
        self.owner_profile = Profile.objects.get(user=self.owner_user)
        self.owner_profile.role = 'OWNER'
        self.owner_profile.save()
        
        # Create user and profile (customer)
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.profile = Profile.objects.get(user=self.user)
        
        # Create city and category
        self.city = City.objects.create(name='Test City')
        self.category = Category.objects.create(name='Test Category')
        
        # Create venue
        self.venue = Venue.objects.create(
            owner=self.owner_profile,
            name='Test Venue',
            address='Test Address',
            type='Indoor',
            price=100000,
            city=self.city,
            category=self.category,
            description='Test description',
            image_url='https://example.com/image.jpg'
        )
    
    def test_old_slots_are_cleaned(self):
        """Test old slots are automatically deleted"""
        # Create an old slot (yesterday)
        old_slot = BookingSlot.objects.create(
            venue=self.venue,
            date=date.today() - timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            is_booked=False
        )
        
        # Create booking for old slot
        Booking.objects.create(
            user=self.profile,
            slot=old_slot,
            total_price=100000
        )
        
        # Access booking page (triggers cleanup)
        self.client.login(username='testuser', password='testpass123')
        self.client.get(reverse('booking:booking_page', args=[self.venue.id]))
        
        # Old slot and booking should be deleted
        self.assertFalse(BookingSlot.objects.filter(id=old_slot.id).exists())
        self.assertFalse(Booking.objects.filter(slot=old_slot).exists())
