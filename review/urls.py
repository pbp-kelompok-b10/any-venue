# In review/urls.py
from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
    path('add/<int:venue_id>/', views.add_review, name='add_review'),
    path('edit/<int:review_id>/', views.edit_review, name='edit_review'),
    path('delete/<int:review_id>/', views.delete_review, name='delete_review'),
    
    path('json/', views.get_reviews_json, name='get_reviews_json'),
    path('json/<int:review_id>/', views.get_review_json_by_id, name='get_review_json_by_id'),
    
    path('testpage/', views.show_review_page, name='show_review_page'),
]