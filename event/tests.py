from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
import json
from datetime import timedelta
from event.models import Event, Registration
from venue.models import Venue, City, Category
from account.models import Profile

class EventTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner_user = User.objects.create_user(username='testowner', password='password123')
        self.owner_profile = Profile.objects.get(user=self.owner_user)
        self.owner_profile.role = 'OWNER'
        self.owner_profile.save()
        self.normal_user = User.objects.create_user(username='testuser', password='password123')
        self.normal_profile = Profile.objects.get(user=self.normal_user)
        self.city = City.objects.create(name='Test City')
        self.category = Category.objects.create(name='Test Sport')
        self.venue = Venue.objects.create(
            owner=self.owner_profile, name='Test Venue', price=100000,
            type='Indoor', city=self.city, category=self.category, address='123 Test Street'
        )
        self.event = Event.objects.create(
            owner=self.owner_profile, venue=self.venue, name='Test Event',
            date=timezone.now().date() + timedelta(days=5),
            start_time=timezone.now().time(), description='A test event.'
        )

    def test_event_model_creation(self):
        self.assertEqual(self.event.name, 'Test Event')
        self.assertEqual(self.event.owner, self.owner_profile)
        self.assertEqual(self.event.venue_name, 'Test Venue')
        self.assertEqual(self.event.venue_type, 'Indoor')
        self.assertEqual(str(self.event), f"Test Event di Test Venue ({self.event.date})")

    def test_registration_model_and_signal(self):
        self.assertEqual(self.event.registered_count, 0)
        self.assertEqual(self.event.booked_slots, 0)
        Registration.objects.create(user=self.normal_user, event=self.event)
        self.event.refresh_from_db()
        self.assertEqual(self.event.registered_count, 1)
        self.assertEqual(self.event.booked_slots, 1)

    def test_show_event_page_authenticated(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('event:show_event'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'show_event.html')

    def test_event_detail_page(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('event:event_detail', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Event')

    def test_create_event_view_valid_date(self):
        self.client.login(username='testowner', password='password123')
        
        future_date = timezone.now().date() + timedelta(days=3)

        event_data = {
            'name': 'New Event via Test',
            'description': 'A new description.',
            'venue': self.venue.id,
            'date': future_date,
            'start_time': '10:00',
            'thumbnail': 'http://example.com/image.jpg',
        }
        response = self.client.post(reverse('event:create_event'), event_data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Event.objects.filter(name='New Event via Test').exists())

    def test_create_event_with_invalid_date_today(self):
        self.client.login(username='testowner', password='password123')
        event_data = {
            'name': 'Event Today Invalid',
            'venue': self.venue.id,
            'date': timezone.now().date(),
            'start_time': '11:00',
        }
        response = self.client.post(reverse('event:create_event'), event_data)
        self.assertEqual(response.status_code, 400) 
        errors = response.json().get('errors')
        self.assertIn('date', errors)
        self.assertEqual(errors['date'][0], "The event date must be in the future (starting from tomorrow).")

    def test_create_event_with_invalid_date_past(self):
        self.client.login(username='testowner', password='password123')
        yesterday = timezone.now().date() - timedelta(days=1)
        event_data = {
            'name': 'Event Past Invalid',
            'venue': self.venue.id,
            'date': yesterday,
            'start_time': '12:00',
        }
        response = self.client.post(reverse('event:create_event'), event_data)
        self.assertEqual(response.status_code, 400)
        errors = response.json().get('errors')
        self.assertIn('date', errors)
        self.assertEqual(errors['date'][0], "The event date must be in the future (starting from tomorrow).")

    def test_update_event_view(self):
        self.client.login(username='testowner', password='password123')
        updated_data = { 'name': 'Updated Event Name', 'description': self.event.description, 'venue': self.venue.id, 'date': self.event.date.strftime('%Y-%m-%d'), 'start_time': self.event.start_time.strftime('%H:%M'), }
        response = self.client.put(reverse('event:update_event', args=[self.event.id]), data=json.dumps(updated_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, 'Updated Event Name')

    def test_update_event_unauthorized(self):
        self.client.login(username='testuser', password='password123')
        updated_data = {'name': 'Unauthorized Update'}
        response = self.client.put(reverse('event:update_event', args=[self.event.id]), data=json.dumps(updated_data), content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_delete_event_view(self):
        self.client.login(username='testowner', password='password123')
        response = self.client.delete(reverse('event:delete_event', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())

    def test_join_event_view(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('event:join_event', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Registration.objects.filter(user=self.normal_user, event=self.event).exists())

    def test_owner_cannot_join_event(self):
        self.client.login(username='testowner', password='password123')
        response = self.client.post(reverse('event:join_event', args=[self.event.id]))
        self.assertEqual(response.status_code, 400)
        self.assertIn("Owners cannot join events", response.json()['message'])

    def test_json_endpoints(self):
        self.client.login(username='testuser', password='password123')
        response_all = self.client.get(reverse('event:show_event_json'))
        self.assertEqual(response_all.status_code, 200)
        self.assertIsInstance(response_all.json(), list)
        response_by_id = self.client.get(reverse('event:show_event_json_by_id', args=[self.event.id]))
        self.assertEqual(response_by_id.status_code, 200)
        self.assertEqual(response_by_id.json()[0]['name'], 'Test Event')