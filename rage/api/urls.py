from django.urls import path

from rage.api.views import get_regions_by_pole, get_districts_by_region

urlpatterns = [
    # Patient URLs
    path('api/regions/', get_regions_by_pole, name='api_regions'),
    path('api/districts/', get_districts_by_region, name='api_districts'),
]