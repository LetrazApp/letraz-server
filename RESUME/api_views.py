from rest_framework.decorators import api_view
from rest_framework.response import Response

from RESUME.models import Resume, Education, Experience
from RESUME.serializers import ResumeShortSerializer, ResumeFullSerializer, EducationFullSerializer, \
    ExperienceFullSerializer


@api_view(['GET'])
def resume_crud(request, user_id: str, resume_id: str | None = None):
    if request.method == 'GET':
        # If resume id is not provided send all resumes for the user
        if not resume_id:
            return Response(
                ResumeShortSerializer(Resume.objects.filter(user__id=user_id), many=True).data
            )
        else:
            resume_by_user_and_resume_id: Resume = Resume.objects.filter(
                user__id=str(user_id), id=resume_id
            ).first()
            return Response(ResumeFullSerializer(resume_by_user_and_resume_id).data)


@api_view(['GET'])
def education_crud(request, user_id: str, resume_id: str, education_id: str | None = None):
    if request.method == 'GET':
        # If resume id is not provided send all resumes for the user
        if not education_id:
            return Response(
                EducationFullSerializer(Education.objects.filter(
                    user__id=user_id, resume_section__resume__id=resume_id
                ), many=True).data
            )
        else:
            education = Education.objects.filter(
                user__id=user_id, resume_section__resume__id=resume_id, id=education_id
            ).first()
            return Response(EducationFullSerializer(education).data)


@api_view(['GET'])
def experience_crud(request, user_id: str, resume_id: str, experience_id: str | None = None):
    if request.method == 'GET':
        # If resume id is not provided send all resumes for the user
        if not experience_id:
            return Response(
                ExperienceFullSerializer(Experience.objects.filter(
                    user__id=user_id, resume_section__resume__id=resume_id
                ), many=True).data
            )
        else:
            experience = Experience.objects.filter(
                user__id=user_id, resume_section__resume__id=resume_id
            ).first()
            return Response(ExperienceFullSerializer(experience).data)
