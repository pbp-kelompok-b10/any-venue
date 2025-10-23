from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date, time, timedelta
from .models import BookingSlot  

from venue.models import Venue

@receiver(post_save, sender=Venue)
def create_default_slots(sender, instance, created, **kwargs):
    """Generate slot otomatis 1 minggu ke depan setelah venue baru dibuat"""
    if not created:
        return

    start_hour = 8  
    end_hour = 22   
    days_ahead = 7  

    for i in range(days_ahead):
        d = date.today() + timedelta(days=i)
        for h in range(start_hour, end_hour):
            BookingSlot.objects.get_or_create(
                venue=instance,
                date=d,
                start_time=time(hour=h),
                end_time=time(hour=h + 1),
            )
