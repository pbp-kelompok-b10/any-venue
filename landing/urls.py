from django.urls import path
from landing.views import (
    show_main, features_preview, header_test, booking_preview_test
)

app_name = 'landing'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('features/', features_preview, name='features_preview'),
    path('header/', header_test, name='header_test'),
    path('booking-preview/', booking_preview_test, name='booking_preview_test'),
]