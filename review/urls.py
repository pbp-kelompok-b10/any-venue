from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
    path('add/<int:venue_id>/', views.add_review, name='add_review'),
    path('edit/<int:review_id>/', views.edit_review, name='edit_review'),
    path('delete/<int:review_id>/', views.delete_review, name='delete_review'),
    
    path('add-flutter/<int:venue_id>/', views.add_review_flutter, name='add_review_flutter'),
    path('edit-flutter/<int:review_id>/', views.edit_review_flutter, name='edit_review_flutter'),
    path('delete-flutter/<int:review_id>/', views.delete_review_flutter, name='delete_review_flutter'),
    
    path('json/', views.get_reviews_json, name='get_reviews_json'),
    path('json/my/', views.get_my_reviews_json, name='get_my_reviews_json'),
    path('json/venue/<int:venue_id>/', views.get_reviews_by_venue, name='get_reviews_by_venue'),
    path('json/venue/<int:venue_id>/my/', views.get_my_review_by_venue, name='get_my_review_by_venue'),
    path('json/<int:review_id>/', views.get_json_by_id, name='get_json_by_id'),

]