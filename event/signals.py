from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Registration, Event

@receiver([post_save, post_delete], sender=Registration)
def update_registered_count(sender, instance, **kwargs):
    event = instance.event
    # Hitung ulang jumlah peserta berdasarkan data Registration
    event.booked_slots = event.registrations.count()
    event.save(update_fields=['booked_slots'])