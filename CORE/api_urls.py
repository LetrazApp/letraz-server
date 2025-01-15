from django.urls import path
from . import api_views

urlpatterns = [
    path('health/', api_views.health_check),
    path('error-example/', api_views.error_example),
    path('error-list-example/', api_views.error_list_example),
    path('waitlist/', api_views.waitlist_crud),
]
