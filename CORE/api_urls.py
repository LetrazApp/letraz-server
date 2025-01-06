from django.urls import path
from . import api_views

urlpatterns = [
    path('health/', api_views.health_check),
    path('error-exapmple/', api_views.error_example),
    path('error-list-exapmple/', api_views.error_list_example),
]
