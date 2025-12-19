from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('', views.profile_page, name='profile_page'),
    path('api/venues/', views.get_venues_json, name='get_venues_json'),
    path('api/bookings/', views.get_bookings_json, name='get_bookings_json'),
    path('api/reviews/', views.get_reviews_json, name='get_reviews_json'),
    path("api/edit-profile/", views.edit_profile, name="edit_profile_api"),
    path("api/delete-account/", views.delete_account, name="delete-account"),
    path("api/profile/edit/", views.edit_profile_flutter, name="edit_profile"),
    path("api/profile/delete/", views.delete_profile_flutter, name="delete_profile"),
    path("api/profile/", views.user_profile_api, name="user_profile_api"),
]