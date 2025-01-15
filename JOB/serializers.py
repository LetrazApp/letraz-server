from rest_framework import serializers
from JOB.models import Job


class JobShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = (
            'id', 'job_url', 'title', 'company_name', 'location',
            'currency', 'salary_max', 'salary_min', 'description'
        )
        read_only_fields = ['id']


class JobFullSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = (
            'id', 'job_url', 'title', 'company_name', 'location',
            'currency', 'salary_max', 'salary_min', 'requirements',
            'description', 'responsibilities', 'benefits'
        )
        read_only_fields = ['id']
