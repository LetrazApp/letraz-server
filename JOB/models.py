from django.db import models
from nanoid import generate as generate_nanoid


# Create your models here.

def generate_job_id():
    nanoid = generate_nanoid()
    while Job.objects.filter(id=f'job_{nanoid}'):
        nanoid = generate_nanoid()
    return f'job_{nanoid}'


class Job(models.Model):
    id = models.CharField(max_length=25, primary_key=True, default=generate_job_id, editable=False)
    job_url = models.CharField(max_length=1000, blank=True, null=True)
    title = models.CharField(max_length=250)
    company_name = models.CharField(max_length=250)
    location = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(max_length=5, blank=True, null=True)
    salary_max = models.PositiveBigIntegerField(blank=True, null=True)
    salary_min = models.PositiveBigIntegerField(blank=True, null=True)
    requirements = models.JSONField(blank=True, null=True)
    description = models.CharField(max_length=3000, blank=True, null=True)  # TODO: May need to change the length
    responsibilities = models.JSONField(blank=True, null=True)
    benefits = models.JSONField(blank=True, null=True)
