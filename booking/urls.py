from django.shortcuts import redirect
from django.urls import path
from . import views

app_name = "booking"

urlpatterns = [
    path('', lambda request: redirect('venue:venue_main')),
    path('<int:venue_id>/', views.booking_page, name='booking_page'),
    path('slots/<int:venue_id>/', views.get_slots, name='get_slots'),
    path('create/', views.create_booking, name='create_booking'),
    path('cancel/', views.cancel_booking, name='cancel_booking'),
    path('json/', views.get_booking_json, name='get_booking_json'),
    path('mybookings/json/', views.get_user_bookings_json, name='get_user_bookings_json'),
    path('create-flutter/', views.create_booking_flutter, name='create_booking_flutter'),
    path('cancel-flutter/', views.cancel_booking_flutter, name='cancel_booking_flutter'),
]

