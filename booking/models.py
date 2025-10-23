from django.db import models
from account.models import Profile
from venue.models import Venue

class BookingSlot(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="slots")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.venue.name} | {self.date} | {self.start_time}-{self.end_time}"

class Booking(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="bookings")
    slot = models.ForeignKey(BookingSlot, on_delete=models.CASCADE)
    total_price = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.user.username} - {self.slot.venue.name} ({self.slot.date})"
