from rest_framework import serializers
from JOB.models import Job


class JobShortSerializer(serializers.ModelSerializer):
    salary = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    class Meta:
        model = Job
        fields = (
            'id', 'job_url', 'title', 'company_name', 'location',
            'salary', 'description', 'status'
        )
        read_only_fields = ['id']

    @staticmethod
    def get_salary(job: Job):
        return {'max': job.salary_max, 'min': job.salary_min, 'currency': job.currency}


    @staticmethod
    def get_status(job: Job):
        return job.get_status_display()


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
    status = serializers.SerializerMethodField()
    class Meta:
        model = Job
        fields = (
            'id', 'job_url', 'title', 'company_name', 'location',
            'salary', 'requirements',
            'description', 'responsibilities', 'benefits', 'status'
        )
        read_only_fields = ['id']

    @staticmethod
    def get_status(job: Job):
        return job.get_status_display()