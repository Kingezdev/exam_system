from django.urls import path
from . import views

app_name = 'venues'

urlpatterns = [
    # Venue management
    path('', views.venue_list, name='venue_list'),
    path('<int:venue_id>/', views.venue_detail, name='venue_detail'),
    path('create/', views.venue_create, name='venue_create'),
    path('<int:venue_id>/update/', views.venue_update, name='venue_update'),
    
    # Venue availability
    path('availability/', views.availability, name='availability'),
    
    # Venue images
    path('<int:venue_id>/upload-image/', views.upload_venue_image, name='upload_image'),
    
    # Venue blocking
    path('<int:venue_id>/block/', views.create_venue_block, name='create_block'),
    path('blocks/', views.block_list, name='block_list'),
    
    # Venue ratings
    path('<int:venue_id>/rate/', views.rate_venue, name='rate_venue'),
    path('ratings/', views.rating_list, name='rating_list'),
    
    # Venue layouts
    path('<int:venue_id>/layout/', views.create_layout, name='create_layout'),
    path('layouts/', views.layout_list, name='layout_list'),
    
    # Available venues API
    path('available/', views.available_venues, name='available_venues'),
]
