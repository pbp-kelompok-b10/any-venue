from django.urls import path
from venue.views import (
    show_main, show_details, get_venues_json, get_venue_json_by_id, 
    add_venue_ajax, edit_venue_ajax, delete_venue_ajax,
    proxy_image, create_venue_flutter, edit_venue_flutter,
    delete_venue_flutter, get_venues_flutter, get_venue_detail_flutter, 
    get_cities_flutter, get_categories_flutter,
)

app_name = 'venue'

urlpatterns = [
    path('', show_main, name='venue_main'),
    path('detail/<int:id>/', show_details, name='venue_detail'),
    path('api/venues/', get_venues_json, name='api_get_venues'),
    path('api/venue/<int:id>/', get_venue_json_by_id, name='api_get_venue_detail'),
    path('api/venues/add/', add_venue_ajax, name='api_add_venue'),
    path('api/venues/edit/<int:id>/', edit_venue_ajax, name='api_edit_venue'),
    path('api/venues/delete/<int:id>/', delete_venue_ajax, name='api_delete_venue'),
    path('proxy-image/', proxy_image, name='proxy_image'),
    path('api/venues-flutter/', get_venues_flutter, name='get_venues_flutter'),
    path('api/venue-detail-flutter/<int:id>/', get_venue_detail_flutter, name='get_venue_detail_flutter'),
    path('api/cities-flutter/', get_cities_flutter, name='get_cities_flutter'),
    path('api/categories-flutter/', get_categories_flutter, name='get_categories_flutter'),
    path('api/create-flutter/', create_venue_flutter, name='create_venue_flutter'),
    path("api/edit-flutter/<int:id>/", edit_venue_flutter, name="edit_venue_flutter"),
    path("api/delete-flutter/<int:id>/", delete_venue_flutter, name="delete_venue_flutter"),
]