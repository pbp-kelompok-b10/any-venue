from django.contrib import admin
from .models import BookingSlot, Booking

admin.site.register(Booking)
admin.site.register(BookingSlot)

