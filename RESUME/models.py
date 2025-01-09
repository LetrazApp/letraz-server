import uuid
from django.db import models
from nanoid import generate
from CORE.models import Country
from PROFILE.models import UserInfo
from JOB.models import Job
from nanoid import generate as generate_nanoid


# Create your models here.
def generate_resume_id():
    nanoid = generate_nanoid()
    while Resume.objects.filter(id=f'job_{nanoid}'):
        nanoid = generate_nanoid()
    return f'rsm_{nanoid}'


class Resume(models.Model):
    id = models.CharField(max_length=25, primary_key=True, default=generate_resume_id, editable=False)
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    base = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user_id', 'job_id')


class Education(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    institution_name = models.CharField(max_length=250)
    field_of_study = models.CharField(max_length=250)
    degree = models.CharField(max_length=250)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    started_from_month = models.PositiveSmallIntegerField()
    started_from_year = models.PositiveSmallIntegerField()
    finished_at_month = models.PositiveSmallIntegerField()
    finished_at_year = models.PositiveSmallIntegerField()
    current = models.BooleanField(default=False)
    description = models.TextField(max_length=3000)  # TODO: May need to change the length
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Experience(models.Model):
    class EmploymentType(models.TextChoices):
        FULL_TIME = 'flt',
        PART_TIME = 'prt',
        CONTRACT = 'con',
        INTERNSHIP = 'int',
        FREELANCE = 'fre',
        SELF_EMPLOYED = 'sel',
        VOLUNTEER = 'vol',
        TRAINEE = 'tra'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=250, blank=True, null=True)
    job_title = models.CharField(max_length=250, blank=True, null=True)
    employment_type = models.CharField(max_length=3, choices=EmploymentType.choices, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    started_from_month = models.PositiveSmallIntegerField()
    started_from_year = models.PositiveSmallIntegerField()
    finished_at_month = models.PositiveSmallIntegerField()
    finished_at_year = models.PositiveSmallIntegerField()
    current = models.BooleanField(default=False)
    description = models.TextField(max_length=3000)  # TODO: May need to change the length
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
