from django.db import models
from django.contrib.auth.models import User
from venue.models import Venue

# Create your models here.
class Event(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event')
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='event')
    thumbnail = models.URLField(blank=True, null=True)
    name = models.CharField(max_length=100)
    date = models.DateField()
    start_time = models.TimeField()
    description = models.TextField(blank=True)
    total_slots = models.PositiveIntegerField(default=0)
    booked_slots = models.PositiveIntegerField(default=0)

    @property
    def venue_type(self):
        return self.venue.type
		
    @property
    def venue_name(self):
        return self.venue.name
    
    @property
    def venue_address(self):
        return self.venue.address
    
    @property
    def available_slots(self):
        return max(self.total_slots - self.booked_slots, 0)

    def __str__(self):
        return f"{self.name} di {self.venue.name} ({self.date})"