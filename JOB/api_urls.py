from django.urls import path, include
from . import api_views

urlpatterns = [
    path('<str:job_id>/', api_views.job_crud),
]
