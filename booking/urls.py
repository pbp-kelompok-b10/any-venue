from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('<int:venue_id>/', views.booking_page, name='booking_page'),
    path('slots/<int:venue_id>/', views.get_slots, name='get_slots'),
    path('create/', views.create_booking, name='create_booking'),
    path('cancel/', views.cancel_booking, name='cancel_booking'),
]

