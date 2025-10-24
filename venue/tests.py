import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Venue, City, Category
from account.models import Profile

class VenueTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testowner', password='password123')
        self.owner_profile = Profile.objects.get(user=self.user)
        self.owner_profile.role = 'OWNER'
        self.owner_profile.save()
        
        self.city = City.objects.create(name='Jakarta')
        self.category = Category.objects.create(name='Futsal')
        
        self.venue = Venue.objects.create(
            owner=self.owner_profile,
            name='Test Venue',
            price=150000,
            city=self.city,
            category=self.category,
            type='Indoor',
            address='Jl. Test No. 1, Jakarta',
            description='Venue untuk testing.',
            image_url='https://example.com/image.jpg'
        )
        
        self.client = Client()

    def test_city_creation(self):
        self.assertEqual(self.city.name, 'Jakarta')
        self.assertEqual(str(self.city), 'Jakarta')

    def test_category_creation(self):
        self.assertEqual(self.category.name, 'Futsal')
        self.assertEqual(str(self.category), 'Futsal')

    def test_venue_creation(self):
        venue = Venue.objects.get(id=self.venue.id)
        self.assertEqual(venue.name, 'Test Venue')
        self.assertEqual(str(venue), 'Test Venue')
        self.assertEqual(venue.owner, self.owner_profile)
        self.assertEqual(venue.price, 150000)
        self.assertEqual(venue.city, self.city)
        self.assertEqual(venue.category, self.category)
        self.assertEqual(venue.type, 'Indoor')

    def test_venue_main_url_is_exist(self):
        self.client.login(username='testowner', password='password123')
        response = self.client.get(reverse('venue:venue_main'))
        self.assertEqual(response.status_code, 200)

    def test_venue_main_using_main_template(self):
        self.client.login(username='testowner', password='password123')
        response = self.client.get(reverse('venue:venue_main'))
        self.assertTemplateUsed(response, 'venue_main.html')

    def test_venue_detail_url_is_exist(self):
        self.client.login(username='testowner', password='password123')
        response = self.client.get(reverse('venue:venue_detail', args=[self.venue.id]))
        self.assertEqual(response.status_code, 200)

    def test_venue_details_using_detail_template(self):
        self.client.login(username='testowner', password='password123')
        response = self.client.get(reverse('venue:venue_detail', args=[self.venue.id]))
        self.assertTemplateUsed(response, 'venue_details.html')

    def test_venue_detail_nonexistent(self):
        self.client.login(username='testowner', password='password123')
        response = self.client.get(reverse('venue:venue_detail', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_page(self):
        response = self.client.get('/halaman_ini_pasti_tidak_ada/')
        self.assertEqual(response.status_code, 404)

    def test_api_get_venues_json(self):
        response = self.client.get(reverse('venue:api_get_venues'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = json.loads(response.content)
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]['name'], 'Test Venue')

    def test_api_get_venue_detail_json(self):
        response = self.client.get(reverse('venue:api_get_venue_detail', args=[self.venue.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = json.loads(response.content)
        self.assertEqual(data['name'], self.venue.name)
        self.assertEqual(data['id'], self.venue.id)

    def test_api_add_venue_ajax(self):
        self.client.login(username='testowner', password='password123')
        venue_count_before = Venue.objects.count()
        
        new_venue_data = {
            'name': 'Venue Ajax Baru',
            'price': 200000,
            'city': self.city.name, 
            'category': self.category.name,
            'type': 'Outdoor',
            'address': 'Jl. Ajax No. 2',
            'description': 'Venue baru via AJAX.',
            'image_url': 'https://example.com/ajax.jpg'
        }
        
        response = self.client.post(
            reverse('venue:api_add_venue'),
            json.dumps(new_venue_data),  
            content_type='application/json' 
        )
        
        self.assertIn(response.status_code, [200, 201])

        self.assertEqual(Venue.objects.count(), venue_count_before + 1)
        
        new_venue = Venue.objects.get(name='Venue Ajax Baru')
        self.assertEqual(new_venue.price, 200000)
        self.assertEqual(new_venue.type, 'Outdoor')
        
        self.assertEqual(new_venue.city, self.city)
        self.assertEqual(new_venue.category, self.category)

    def test_api_add_venue_sad_path_invalid_city(self):
        # Login sebagai owner
        self.client.login(username='testowner', password='password123')
        
        venue_count_before = Venue.objects.count()

        invalid_venue_data = {
            'name': 'Venue Gagal',
            'price': 100000,
            'city': 'Kota-Yang-Tidak-Ada', 
            'category': self.category.name, 
            'type': 'Indoor',
            'address': 'Jl. Gagal',
            'description': 'Venue gagal tes.',
            'image_url': 'https://example.com/gagal.jpg'
        }
        
        response = self.client.post(
            reverse('venue:api_add_venue'),
            json.dumps(invalid_venue_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Venue.objects.count(), venue_count_before)
        data = json.loads(response.content)
        self.assertIn('city', data)

    def test_api_edit_venue_ajax(self):
        self.client.login(username='testowner', password='password123')
    
        edit_data = {
            'name': 'Test Venue (Edited)', 
            'price': 99999,
            'city': self.city.name,
            'category': self.category.name,
            'type': 'Outdoor', 
            'address': 'Jl. Test No. 1, Jakarta (Edited)',
            'description': 'Venue untuk testing (Edited).',
            'image_url': 'https://example.com/image_edited.jpg'
        }
        
        response = self.client.put(
            reverse('venue:api_edit_venue', args=[self.venue.id]),
            json.dumps(edit_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.venue.refresh_from_db()
        self.assertEqual(self.venue.name, 'Test Venue (Edited)')
        self.assertEqual(self.venue.price, 99999)
        self.assertEqual(self.venue.type, 'Outdoor')

    def test_api_delete_venue_ajax(self):
        self.client.login(username='testowner', password='password123')
        
        venue_count_before = Venue.objects.count()

        response = self.client.delete(
            reverse('venue:api_delete_venue', args=[self.venue.id])
        )
        
        self.assertIn(response.status_code, [200, 204])

        self.assertEqual(Venue.objects.count(), venue_count_before - 1)
        self.assertEqual(Venue.objects.count(), 0)

        with self.assertRaises(Venue.DoesNotExist):
            Venue.objects.get(id=self.venue.id)