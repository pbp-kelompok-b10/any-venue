from django.urls import path
from . import views


app_name = "booking"


urlpatterns = [
    path("<int:court_id>/", views.booking_page, name="booking_page"),
    path("<int:court_id>/api/slots/", views.get_slots, name="get_slots"),
    path("<int:court_id>/api/book/", views.make_booking, name="make_booking"),
    path("<int:court_id>/api/cancel/", views.cancel_booking, name="cancel_booking"),
]