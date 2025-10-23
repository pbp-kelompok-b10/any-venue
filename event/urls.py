from django.urls import path
from event.views import (show_main)

app_name = 'event'

urlpatterns = [
    path('', show_main, name='event_main'),
]