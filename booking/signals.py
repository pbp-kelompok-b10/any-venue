from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date, time, timedelta
from .models import Court, BookingSlot


@receiver(post_save, sender=Court)
def create_default_slots(sender, instance, created, **kwargs):
	if not created:
		return


	start_hour = 8
	end_hour = 22
	days_ahead = 7


	for i in range(days_ahead):
		d = date.today() + timedelta(days=i)
		for h in range(start_hour, end_hour):
			BookingSlot.objects.get_or_create(
				court=instance,
				date=d,
				start_time=time(hour=h),
				end_time=time(hour=h + 1),
			)