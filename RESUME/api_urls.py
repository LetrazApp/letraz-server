from django.urls import path, include
from . import api_views

urlpatterns = [
    path('', api_views.resume_crud),
    path('<str:resume_id>/', api_views.resume_crud),
    path('<str:resume_id>/education/', api_views.education_crud),
    path('<str:resume_id>/education/<str:education_id>/', api_views.education_crud),
    path('<str:resume_id>/experience/', api_views.experience_crud),
    path('<str:resume_id>/experience/<str:experience_id>/', api_views.experience_crud),
]
