from django.urls import path
from account.views import profile_page

urlpatterns = [
    path("", profile_page, name="profile_page"),
    # path("delete-booking/", views.delete_booking, name="delete_booking"),
]
