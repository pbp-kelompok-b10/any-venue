from django.contrib import admin
from .models import City, Category, Venue

# Register your models here.
admin.site.register(City)
admin.site.register(Category)
admin.site.register(Venue)