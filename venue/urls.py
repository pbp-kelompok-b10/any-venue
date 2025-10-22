from django.urls import path
from venue.views import (
    show_details,
)

app_name = 'venue'

urlpatterns = [
    path('', show_details, name='show_details'),
]