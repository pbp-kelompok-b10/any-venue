from django.db import models
from django.contrib.auth.models import User
from venue.models import Venue


class Court(models.Model):
	venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="courts")
	name = models.CharField(max_length=100)

	def __str__(self):
		return f"{self.name} - {self.venue.name}"


class BookingSlot(models.Model):
	court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name="slots")
	date = models.DateField()
	start_time = models.TimeField()
	end_time = models.TimeField()
	is_booked = models.BooleanField(default=False)

	class Meta:
		ordering = ["date", "start_time"]
		unique_together = ("court", "date", "start_time", "end_time")

	def __str__(self):
		return f"{self.court.name} | {self.date} {self.start_time}-{self.end_time}"


class Booking(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
	slot = models.ForeignKey(BookingSlot, on_delete=models.CASCADE)
	total_price = models.IntegerField()
	created_at = models.DateTimeField(auto_now_add=True)

	@property
	def venue(self):
		return self.slot.court.venue

	@property
	def slot_info(self):
		return {
			"date": self.slot.date.strftime("%Y-%m-%d"),
			"start": self.slot.start_time.strftime("%H:%M"),
			"end": self.slot.end_time.strftime("%H:%M"),
			"venue": self.venue.name,
			"venue_type": self.venue.type,
			"court": self.slot.court.name,
			"price": self.total_price,
		}

	def __str__(self):
		return f"{self.user.username} - {self.slot}"