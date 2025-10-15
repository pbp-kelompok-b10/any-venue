from django.urls import path
from landing.views import (
    show_main, 
)

app_name = 'landing'

urlpatterns = [
    path('', show_main, name='show_main'),
]