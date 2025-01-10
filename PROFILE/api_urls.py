from django.urls import path, include
from . import api_views

urlpatterns = [
    path('', api_views.profile_crud),
]
