from django.urls import path
from event.views import (
    show_event,
    show_event_json,
    show_event_json_by_id,
    create_event,
    show_event_detail,
    update_event,
    delete_event
)


app_name = 'event'

urlpatterns = [
    path('', show_event, name='show_event'),
    path('json/', show_event_json, name='show_event_json'),
    path('json/<int:id>/', show_event_json_by_id, name='show_event_json_by_id'),
    path('create/', create_event, name='create_event'),
    path('<int:event_id>/', show_event_detail, name='show_event_detail'),
    path('update/<int:event_id>/', update_event, name='update_event'),
    path('delete/<int:event_id>/', delete_event, name='delete_event'),
]
