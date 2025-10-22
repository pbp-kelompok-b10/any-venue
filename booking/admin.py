from django.contrib import admin
from .models import Booking

# Register your models here.

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'venue', 'booking_date', 'date_type', 'quantity', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'date_type', 'booking_date', 'created_at']
    search_fields = ['user__username', 'venue__name']
    readonly_fields = ['total_price', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informasi Booking', {
            'fields': ('user', 'venue', 'booking_date', 'date_type')
        }),
        ('Detail Harga', {
            'fields': ('price', 'quantity', 'total_price')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ['user', 'venue']
        return self.readonly_fields
