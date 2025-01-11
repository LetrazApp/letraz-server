from django.urls import path, include
from . import api_views

urlpatterns = [
    path('', api_views.user_info_crud),
    path('<str:user_id>/', api_views.user_info_crud),
]
