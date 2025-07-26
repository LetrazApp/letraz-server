from django.urls import path, include
from rest_framework import routers
from .api_views import ResumeViewSets, EducationViewSets, ExperienceViewSets, ResumeSkillViewSets, ResumeProjectViewSets, ResumeCertificationViewSets, tailor_resume

root_router = routers.DefaultRouter()
root_router.register(r'', ResumeViewSets, basename='resume')

child_router = routers.DefaultRouter()
child_router.register(r'experience', ExperienceViewSets, basename='experience')
child_router.register(r'education', EducationViewSets, basename='education')
child_router.register(r'skill', ResumeSkillViewSets, basename='skill')
child_router.register(r'project', ResumeProjectViewSets, basename='project')
child_router.register(r'certification', ResumeCertificationViewSets, basename='certification')

urlpatterns = [
    path('tailor/', tailor_resume),
    path('', include(root_router.urls)),
    path('<str:resume_id>/', include(child_router.urls)),
]
