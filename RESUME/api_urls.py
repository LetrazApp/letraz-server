from django.urls import path, include
from rest_framework import routers

from .api_views import ResumeViewSets, EducationViewSets, ExperienceViewSets

root_router = routers.DefaultRouter()
root_router.register(r'', ResumeViewSets, basename='resume')

child_router = routers.DefaultRouter()
child_router.register(r'experience', ExperienceViewSets, basename='experience')
child_router.register(r'education', EducationViewSets, basename='education')

urlpatterns = [
    path('', include(root_router.urls)),
    path('<str:resume_id>/', include(child_router.urls)),
]
