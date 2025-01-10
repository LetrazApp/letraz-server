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
    job = models.ForeignKey(Job, on_delete=models.CASCADE, blank=True, null=True)
    base = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user_id', 'job_id')

    def __str__(self):
        return f'{self.id} [{self.user.get_full_name()}]'


class ResumeSection(models.Model):
    class ResumeSectionType(models.TextChoices):
        Education = 'edu'
        Experience = 'exp'
        Others = 'oth'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    index = models.IntegerField()
    type = models.CharField(max_length=3, choices=ResumeSectionType.choices)

    class Meta:
        unique_together = ('resume', 'index')

    def get_context(self):
        if self.type == ResumeSection.ResumeSectionType.Education:
            return self.education
        elif self.type == ResumeSection.ResumeSectionType.Experience:
            return self.experience
        else:
            return None

    def __str__(self):
        return f'{self.type} | {self.resume.id} - {self.index}'


class Education(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    resume_section = models.OneToOneField(ResumeSection, on_delete=models.CASCADE)
    institution_name = models.CharField(max_length=250)
    field_of_study = models.CharField(max_length=250)
    degree = models.CharField(max_length=250, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    started_from_month = models.PositiveSmallIntegerField(null=True, blank=True)
    started_from_year = models.PositiveSmallIntegerField(null=True, blank=True)
    finished_at_month = models.PositiveSmallIntegerField(null=True, blank=True)
    finished_at_year = models.PositiveSmallIntegerField(null=True, blank=True)
    current = models.BooleanField(default=False)
    description = models.TextField(max_length=3000, null=True, blank=True)  # TODO: May need to change the length
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.institution_name}'


class Experience(models.Model):
    class EmploymentType(models.TextChoices):
        FULL_TIME = 'flt'
        PART_TIME = 'prt'
        CONTRACT = 'con'
        INTERNSHIP = 'int'
        FREELANCE = 'fre'
        SELF_EMPLOYED = 'sel'
        VOLUNTEER = 'vol'
        TRAINEE = 'tra'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    resume_section = models.OneToOneField(ResumeSection, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=250)
    job_title = models.CharField(max_length=250)
    employment_type = models.CharField(max_length=3, choices=EmploymentType.choices)
    city = models.CharField(max_length=50, blank=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, blank=True, null=True)
    started_from_month = models.PositiveSmallIntegerField(null=True, blank=True)
    started_from_year = models.PositiveSmallIntegerField(null=True, blank=True)
    finished_at_month = models.PositiveSmallIntegerField(null=True, blank=True)
    finished_at_year = models.PositiveSmallIntegerField(null=True, blank=True)
    current = models.BooleanField(default=False)
    description = models.TextField(max_length=3000, null=True, blank=True)  # TODO: May need to change the length
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.company_name}'
