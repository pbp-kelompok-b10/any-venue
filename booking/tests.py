from django.test import TestCase, Client
from django.contrib.auth.models import User
from datetime import date, time, timedelta
from account.models import Profile
from venue.models import Venue, City, Category
from .models import BookingSlot, Booking
import json
from django.utils import timezone
from booking.views import ensure_slots_for_date


class BookingFlutterAPITest(TestCase):
    def setUp(self):
        self.client = Client()

        # Owner and venue
        owner_user = User.objects.create_user(username='owner_f', password='pass')
        owner_profile = Profile.objects.get(user=owner_user)
        owner_profile.role = 'OWNER'
        owner_profile.save()

        self.user = User.objects.create_user(username='cust_f', password='pass')
        self.profile = Profile.objects.get(user=self.user)

        self.city = City.objects.create(name='CityF')
        self.category = Category.objects.create(name='CatF')
        self.venue = Venue.objects.create(
            owner=owner_profile,
            name='VenueF',
            address='Addr',
            type='Indoor',
            price=150000,
            city=self.city,
            category=self.category,
            description='Desc',
            image_url='https://example.com/img.jpg',
        )

        self.today = timezone.localdate()

    def _login_user(self):
        self.client.login(username='cust_f', password='pass')

    def test_create_booking_flutter_success(self):
        slot = BookingSlot.objects.create(
            venue=self.venue,
            date=self.today + timedelta(days=1),
            start_time=time(8, 0),
            end_time=time(9, 0),
            is_booked=False,
        )
        self._login_user()
        resp = self.client.post(
            reverse('booking:create_booking_flutter'),
            json.dumps({'slots': [slot.id]}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 201)
        body = json.loads(resp.content)
        self.assertEqual(body['status'], 'success')
        slot.refresh_from_db()
        self.assertTrue(slot.is_booked)
        self.assertTrue(Booking.objects.filter(slot=slot, user=self.profile).exists())

    def test_create_booking_flutter_conflict(self):
        slot = BookingSlot.objects.create(
            venue=self.venue,
            date=self.today + timedelta(days=1),
            start_time=time(9, 0),
            end_time=time(10, 0),
            is_booked=True,
        )
        self._login_user()
        resp = self.client.post(
            reverse('booking:create_booking_flutter'),
            json.dumps({'slots': [slot.id]}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 409)

    def test_create_booking_flutter_past_slot_rejected(self):
        slot = BookingSlot.objects.create(
            venue=self.venue,
            date=self.today - timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            is_booked=False,
        )
        self._login_user()
        resp = self.client.post(
            reverse('booking:create_booking_flutter'),
            json.dumps({'slots': [slot.id]}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)

    def test_create_booking_flutter_role_not_user(self):
        # login as owner (not USER role)
        self.client.login(username='owner_f', password='pass')
        slot = BookingSlot.objects.create(
            venue=self.venue,
            date=self.today + timedelta(days=1),
            start_time=time(12, 0),
            end_time=time(13, 0),
            is_booked=False,
        )
        resp = self.client.post(
            reverse('booking:create_booking_flutter'),
            json.dumps({'slots': [slot.id]}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 403)

    def test_cancel_booking_flutter_success(self):
        slot = BookingSlot.objects.create(
            venue=self.venue,
            date=self.today + timedelta(days=1),
            start_time=time(14, 0),
            end_time=time(15, 0),
            is_booked=True,
        )
        booking = Booking.objects.create(user=self.profile, slot=slot, total_price=self.venue.price)
        self._login_user()
        resp = self.client.post(
            reverse('booking:cancel_booking_flutter'),
            json.dumps({'slot_id': slot.id}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        slot.refresh_from_db()
        self.assertFalse(slot.is_booked)
        self.assertFalse(Booking.objects.filter(id=booking.id).exists())

    def test_cancel_booking_flutter_past_slot_rejected(self):
        slot = BookingSlot.objects.create(
            venue=self.venue,
            date=self.today - timedelta(days=1),
            start_time=time(8, 0),
            end_time=time(9, 0),
            is_booked=True,
        )
        Booking.objects.create(user=self.profile, slot=slot, total_price=self.venue.price)
        self._login_user()
        resp = self.client.post(
            reverse('booking:cancel_booking_flutter'),
            json.dumps({'slot_id': slot.id}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)

    def test_get_slot_venue_flutter(self):
        slot = BookingSlot.objects.create(
            venue=self.venue,
            date=self.today + timedelta(days=2),
            start_time=time(16, 0),
            end_time=time(17, 0),
            is_booked=False,
        )
        self._login_user()
        resp = self.client.get(reverse('booking:get_slot_venue_flutter', args=[slot.id]))
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['venue']['id'], self.venue.id)
from django.urls import reverse

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


class BookingAdditionalTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Owner and venue setup
        owner_user = User.objects.create_user(username='owner2', password='testpass123')
        owner_profile = Profile.objects.get(user=owner_user)
        owner_profile.role = 'OWNER'
        owner_profile.save()

        # Customer user
        self.user = User.objects.create_user(username='cust', password='testpass123')
        self.profile = Profile.objects.get(user=self.user)

        self.city = City.objects.create(name='City2')
        self.category = Category.objects.create(name='Cat2')
        self.venue = Venue.objects.create(
            owner=owner_profile,
            name='Venue2',
            address='Addr',
            type='Indoor',
            price=250000,
            city=self.city,
            category=self.category,
            description='Desc',
            image_url='https://example.com/img.jpg'
        )

    def test_get_slots_missing_date_returns_empty(self):
        url = reverse('booking:get_slots', args=[self.venue.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data, [])

    def test_get_slots_creates_on_demand_within_horizon(self):
        # Pick a date 3 days ahead with no pre-created slots
        target = date.today() + timedelta(days=3)
        url = reverse('booking:get_slots', args=[self.venue.id])
        resp = self.client.get(url, {'date': target.strftime('%Y-%m-%d')})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        # Expect slots from 08:00 to 21:00 (14 slots)
        self.assertGreaterEqual(len(data), 10)
        self.assertTrue(any(s['start_time'] == '08:00' for s in data))

    def test_get_slots_does_not_create_beyond_horizon(self):
        # Beyond 30-day horizon, should not auto-create
        target = date.today() + timedelta(days=40)
        url = reverse('booking:get_slots', args=[self.venue.id])
        resp = self.client.get(url, {'date': target.strftime('%Y-%m-%d')})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data, [])

    def test_get_slots_filters_past_today_slots_and_cleans_booking(self):
        # Create a slot for today that already ended
        now = timezone.localtime()
        end_past = (now - timedelta(hours=1)).time()
        start_past = (now - timedelta(hours=2)).time()
        slot = BookingSlot.objects.create(
            venue=self.venue,
            date=timezone.localdate(),
            start_time=start_past,
            end_time=end_past,
            is_booked=True,
        )
        # Assign a booking for cleanup check
        Booking.objects.create(user=self.profile, slot=slot, total_price=self.venue.price)

        url = reverse('booking:get_slots', args=[self.venue.id])
        resp = self.client.get(url, {'date': timezone.localdate().strftime('%Y-%m-%d')})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        # Past slot should not be returned
        self.assertTrue(all(s['id'] != slot.id for s in data))
        # Booking should be cleaned and slot marked available
        slot.refresh_from_db()
        self.assertFalse(slot.is_booked)
        self.assertFalse(Booking.objects.filter(slot=slot).exists())

    def test_cancel_booking_not_found(self):
        # No booking exists for this slot
        slot = BookingSlot.objects.create(
            venue=self.venue,
            date=date.today() + timedelta(days=1),
            start_time=time(8, 0),
            end_time=time(9, 0),
            is_booked=False,
        )
        self.client.login(username='cust', password='testpass123')
        resp = self.client.post(
            reverse('booking:cancel_booking'),
            json.dumps({'slot_id': slot.id}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)['status'], 'not_found')

    def test_create_booking_empty_slots_returns_zero_total(self):
        self.client.login(username='cust', password='testpass123')
        resp = self.client.post(
            reverse('booking:create_booking'),
            json.dumps({'slots': []}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content)
        self.assertEqual(body['status'], 'success')
        self.assertEqual(body['total'], 0)

    def test_create_and_cancel_booking_wrong_method_returns_error(self):
        # create_booking via GET
        self.client.login(username='cust', password='testpass123')
        resp_get = self.client.get(reverse('booking:create_booking'))
        self.assertEqual(resp_get.status_code, 200)
        self.assertEqual(json.loads(resp_get.content)['status'], 'error')

        # cancel_booking via GET
        resp_get2 = self.client.get(reverse('booking:cancel_booking'))
        self.assertEqual(resp_get2.status_code, 200)
        self.assertEqual(json.loads(resp_get2.content)['status'], 'error')

    def test_ensure_slots_for_past_date_no_creation(self):
        # Directly exercise helper to cover early return path
        yesterday = date.today() - timedelta(days=1)
        ensure_slots_for_date(self.venue, yesterday)
        self.assertFalse(BookingSlot.objects.filter(venue=self.venue, date=yesterday).exists())
