from django.db import models
from nanoid import generate as generate_nanoid

from CORE.models import Process


# Create your models here.

def generate_job_id():
    nanoid = generate_nanoid()
    while Job.objects.filter(id=f'job_{nanoid}'):
        nanoid = generate_nanoid()
    return f'job_{nanoid}'


class Job(models.Model):
    id = models.CharField(
        max_length=25,
        primary_key=True,
        default=generate_job_id,
        editable=False,
        help_text='The unique identifier for the job entry.'
    )
    job_url = models.CharField(max_length=1000, blank=True, null=True, help_text='The URL of the job posting. (optional)')
    title = models.CharField(max_length=250, help_text='The title of the job as mentioned in the job posting. If not available, a meaningful title would be auto-generated.')
    company_name = models.CharField(max_length=250, help_text='The name of the company that posted the job.')
    location = models.CharField(max_length=100, blank=True, null=True, help_text='The location of the job as mentioned in the job posting. (optional)')
    currency = models.CharField(max_length=5, blank=True, null=True, help_text='The currency code of the salary. (optional)')
    salary_max = models.PositiveBigIntegerField(blank=True, null=True, help_text='The maximum salary of the job as mentioned in the job posting. (optional)')
    salary_min = models.PositiveBigIntegerField(blank=True, null=True, help_text='The minimum salary of the job as mentioned in the job posting. (optional)')
    requirements = models.JSONField(blank=True, null=True, help_text='An array representation of the requirements of the job as mentioned in the job posting. (optional)')
    description = models.CharField(max_length=3000, blank=True, null=True, help_text='The description of the job as mentioned in the job posting. (optional)')  # TODO: May need to change the length
    responsibilities = models.JSONField(blank=True, null=True, help_text='An array representation of the responsibilities the candidate would be undertaking as mentioned in the job posting. (optional)')
    benefits = models.JSONField(blank=True, null=True, help_text='An array representation of the benefits the candidate would get as mentioned in the job posting. (optional)')

    processing = models.BooleanField(default=False)
    process = models.ForeignKey(Process, on_delete=models.SET_NULL, blank=True, null=True)
