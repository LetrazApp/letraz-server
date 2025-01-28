from django.urls import path, include
from . import api_views

urlpatterns = [
    path('', api_views.UserCRUD.as_view()),
]
