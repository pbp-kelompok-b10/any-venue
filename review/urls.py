# In review/urls.py
from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
    # URL for adding a review (requires a venue_id)
    # e.g., /review/add/5/
    path('add/<int:venue_id>/', views.add_review, name='add_review'),

    # URL for editing a review (requires a review_id)
    # e.g., /review/edit/12/
    path('edit/<int:review_id>/', views.edit_review, name='edit_review'),

    # URL for deleting a review (requires a review_id)
    # e.g., /review/delete/12/
    path('delete/<int:review_id>/', views.delete_review, name='delete_review'),
]