from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    # Booking list & detail
    path('', views.booking_list, name='list'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('venue-bookings/', views.venue_bookings, name='venue_bookings'),
    path('<int:booking_id>/', views.booking_detail, name='detail'),
    
    # Create booking
    path('create/<int:venue_id>/', views.create_booking, name='create'),
    
    # Actions
    path('<int:booking_id>/cancel/', views.cancel_booking, name='cancel'),
    path('<int:booking_id>/confirm/', views.confirm_booking, name='confirm'),
    path('<int:booking_id>/complete/', views.complete_booking, name='complete'),
    
    # AJAX API
    path('api/check-availability/', views.check_availability, name='check_availability'),
    
    # JSON API Endpoints (untuk user yang sudah login)
    path('api/json/', views.booking_json, name='booking_json'),
    path('api/venue-bookings/json/', views.venue_bookings_json, name='venue_bookings_json'),
]
