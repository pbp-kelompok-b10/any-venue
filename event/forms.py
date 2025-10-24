from django.utils.html import strip_tags
from django import forms
from event.models import Event
from venue.models import Venue

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'description', 'venue', 'date', 'start_time', 'thumbnail']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['venue'].queryset = Venue.objects.filter(owner=user)
        else:
            self.fields['venue'].queryset = Venue.objects.none()
    
    def clean_name(self):
        name = self.cleaned_data["name"]
        return strip_tags(name)

    def clean_description(self):
        description = self.cleaned_data["description"]
        return strip_tags(description)
