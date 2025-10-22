from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

# Create your models here.

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    DATE_TYPE_CHOICES = [
        ('indoor', 'Indoor'),
        ('outdoor', 'Outdoor'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    venue = models.ForeignKey('venue.Venue', on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateField()
    date_type = models.CharField(max_length=10, choices=DATE_TYPE_CHOICES, default='outdoor')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        
    def __str__(self):
        return f"Booking {self.id} - {self.venue.name if hasattr(self, 'venue') else 'Unknown'} by {self.user.username}"
    
    def clean(self):
        # Validasi booking_date tidak boleh di masa lalu
        if self.booking_date and self.booking_date < timezone.now().date():
            raise ValidationError({'booking_date': 'Tanggal booking tidak boleh di masa lalu.'})
        
        # Cek apakah venue sudah dibooking pada tanggal yang sama
        if self.pk is None:  # Hanya untuk booking baru
            existing_bookings = Booking.objects.filter(
                venue=self.venue,
                booking_date=self.booking_date,
                status__in=['pending', 'confirmed']
            )
            if existing_bookings.exists():
                raise ValidationError({'booking_date': 'Venue sudah dibooking pada tanggal tersebut.'})
    
    def save(self, *args, **kwargs):
        # Hitung total price otomatis
        self.total_price = self.price * self.quantity
        self.full_clean()
        super().save(*args, **kwargs)
    
    def cancel(self):
        """Method untuk cancel booking"""
        if self.status in ['pending', 'confirmed']:
            self.status = 'cancelled'
            self.save()
            return True
        return False
    
    def confirm(self):
        """Method untuk confirm booking (untuk owner)"""
        if self.status == 'pending':
            self.status = 'confirmed'
            self.save()
            return True
        return False
    
    def complete(self):
        """Method untuk menandai booking selesai"""
        if self.status == 'confirmed':
            self.status = 'completed'
            self.save()
            return True
        return False
    
    def is_cancellable(self):
        """Cek apakah booking bisa di-cancel"""
        return self.status in ['pending', 'confirmed']
    
    def is_reviewable(self):
        """Cek apakah booking bisa di-review (sudah selesai dan belum ada review)"""
        return self.status == 'completed' and not hasattr(self, 'review')
