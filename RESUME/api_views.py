from django.db.models import QuerySet
from rest_framework.decorators import api_view
from rest_framework.response import Response
from RESUME.models import Resume, Education, Experience
from RESUME.serializers import ResumeShortSerializer, ResumeFullSerializer, EducationFullSerializer, \
    ExperienceFullSerializer
from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse


@api_view(['GET'])
def resume_crud(request, user_id: str, resume_id: str | None = None):
    if request.method == 'GET':
        print(request.query_params)
        # If resume id is not provided send all resumes for the user
        if request.query_params.get('base') and request.query_params.get('base') == 'true':
            base_resume_qs: QuerySet[Resume] = Resume.objects.filter(user__id=user_id, base=True)
            if base_resume_qs.exists():
                return Response(ResumeFullSerializer(base_resume_qs.first()).data)
            else:
                return ErrorResponse(code=ErrorCode.NOT_FOUND, message='Base Resume not found!').response
        elif resume_id:
            resume_by_user_and_resume_id_qs: QuerySet[Resume] = Resume.objects.filter(
                user__id=str(user_id), id=resume_id
            )
            if resume_by_user_and_resume_id_qs.exists():
                return Response(ResumeFullSerializer(resume_by_user_and_resume_id_qs.first()).data)
            else:
                return ErrorResponse(
                    code=ErrorCode.NOT_FOUND, message='Resume not found!', details={'resume': resume_id}
                ).response
        else:
            return Response(
                ResumeShortSerializer(Resume.objects.filter(user__id=user_id), many=True).data
            )


@api_view(['GET'])
def education_crud(request, user_id: str, resume_id: str, education_id: str | None = None):
    if request.method == 'GET':
        if education_id:
            education_sq: QuerySet[Education] = Education.objects.filter(
                user__id=user_id, resume_section__resume__id=resume_id, id=education_id
            )
            if education_sq.exists():
                return Response(EducationFullSerializer(education_sq.first()).data)
            else:
                return ErrorResponse(
                    code=ErrorCode.NOT_FOUND, message='Education not found!', details={'education': education_id}
                ).response
        else:  # If resume id is not provided send all resumes for the user
            return Response(
                EducationFullSerializer(Education.objects.filter(
                    user__id=user_id, resume_section__resume__id=resume_id
                ), many=True).data
            )


@api_view(['GET'])
def experience_crud(request, user_id: str, resume_id: str, experience_id: str | None = None):
    if request.method == 'GET':
        if experience_id:
            experience_qs: QuerySet[Experience] = Experience.objects.filter(
                user__id=user_id, resume_section__resume__id=resume_id
            )
            if experience_qs.exists():
                return Response(ExperienceFullSerializer(experience_qs.first()).data)
            else:
                return ErrorResponse(
                    code=ErrorCode.NOT_FOUND, message='Experience not found!', details={'experience': experience_id}
                ).response
        else:  # If resume id is not provided send all resumes for the user
            return Response(
                ExperienceFullSerializer(Experience.objects.filter(
                    user__id=user_id, resume_section__resume__id=resume_id), many=True).data
            )
