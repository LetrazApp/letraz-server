from django.urls import path, include
from rest_framework import routers

from .api_views import ResumeCRUD, EducationCRUD, ExperienceViewSets

experience_router = routers.DefaultRouter()
experience_router.register(r'experience', ExperienceViewSets, basename='experience')

urlpatterns = [
    path('', ResumeCRUD.as_view()),
    path('<str:resume_id>/', ResumeCRUD.as_view()),
    path('<str:resume_id>/education/', EducationCRUD.as_view()),
    path('<str:resume_id>/education/<str:education_id>/', EducationCRUD.as_view()),

    path('<str:resume_id>/', include(experience_router.urls)),

]
