from django.urls import path
from . import views

urlpatterns = [
    path('', views.profile_page, name='profile_page'),
    path('api/venues/', views.get_venues_json, name='get_venues_json'),
    path('api/bookings/', views.get_bookings_json, name='get_bookings_json'),
    path('api/reviews/', views.get_reviews_json, name='get_reviews_json'),
]
