from rest_framework import serializers
from JOB.models import Job


class JobShortSerializer(serializers.ModelSerializer):
    salary = serializers.SerializerMethodField()
    class Meta:
        model = Job
        fields = (
            'id', 'job_url', 'title', 'company_name', 'location',
            'salary', 'description', 'processing'
        )
        read_only_fields = ['id']

    @staticmethod
    def get_salary(job: Job):
        return {'max': job.salary_max, 'min': job.salary_min, 'currency': job.currency}


class JobSerializer(serializers.ModelSerializer):
    salary = serializers.SerializerMethodField()
    class Meta:
        model = Job
        fields = (
            'id', 'job_url', 'title', 'company_name', 'location',
            'salary', 'requirements',
            'description', 'responsibilities', 'benefits'
        )
        read_only_fields = ['id']

    @staticmethod
    def get_salary(job: Job):
        return {'max': job.salary_max, 'min': job.salary_min, 'currency': job.currency}

class JobFullSerializer(JobSerializer):
    class Meta:
        model = Job
        fields = (
            'id', 'job_url', 'title', 'company_name', 'location',
            'salary', 'requirements',
            'description', 'responsibilities', 'benefits', 'processing'
        )
        read_only_fields = ['id']
