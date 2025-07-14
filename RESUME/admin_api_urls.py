from django.urls import path
from . import admin_api_views

urlpatterns = [
    path('<str:resume_id>/', admin_api_views.admin_resume_get),
] 