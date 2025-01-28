from django.urls import path
from .api_views import ResumeCRUD, EducationCRUD, ExperienceCRUD

urlpatterns = [
    path('', ResumeCRUD.as_view()),
    path('<str:resume_id>/', ResumeCRUD.as_view()),
    path('<str:resume_id>/education/', EducationCRUD.as_view()),
    path('<str:resume_id>/education/<str:education_id>/', EducationCRUD.as_view()),
    path('<str:resume_id>/experience/', ExperienceCRUD.as_view()),
    path('<str:resume_id>/experience/<str:experience_id>/', ExperienceCRUD.as_view()),
]
