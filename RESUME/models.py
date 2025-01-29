import uuid
from django.db import models
from django.db.models import Q
from CORE.models import Country
from PROFILE.models import User
from JOB.models import Job
from nanoid import generate as generate_nanoid


# Create your models here.
def generate_resume_id():
    nanoid = generate_nanoid()
    while Resume.objects.filter(id=f'job_{nanoid}'):
        nanoid = generate_nanoid()
    return f'rsm_{nanoid}'


class Resume(models.Model):
    id = models.CharField(
        max_length=25,
        primary_key=True,
        default=generate_resume_id,
        editable=False,
        help_text='The unique identifier for the resume entry.'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text='The user who the resume belongs to.')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, blank=True, null=True,
                            help_text='The job the resume is for. (optional in case it\'s a base resume for the user.)')
    base = models.BooleanField(default=False,
                               help_text='Whether the resume is a base resume for the user. One user can ')
    variations = models.ManyToManyField('Resume', related_name='related_resumes', blank=True)
    version = models.IntegerField(default=1, help_text='The version of the resume.')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'job'],
                name="unique_resume_per_job",
                violation_error_message="This job is already have a resume.",
            ),
            models.UniqueConstraint(
                fields=['user', 'base'],
                condition=Q(base=True),
                name="unique_base_resume",
                violation_error_message="Base resume already exists.",
            ),
        ]

    def create_section(self, section_type):
        next_resume_section = self.resumesection_set.all().order_by(
            '-index').first().index + 1 if self.resumesection_set.exists() else 0
        new_resume_section = ResumeSection.objects.create(
            resume_id=self.id, type=section_type, index=next_resume_section
        )
        return new_resume_section

    def generate_next_resume_version(self):
        if self.variations.exists():
            return self.variations.order_by('version').last().version + 1
        return 1

    def __str__(self):
        return f'{self.id} [{self.user.get_full_name()}]'


class ResumeSection(models.Model):
    class ResumeSectionType(models.TextChoices):
        Education = 'edu'
        Experience = 'exp'
        Others = 'oth'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='The unique identifier for the resume section entry.'
    )
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, help_text='The resume the section belongs to.')
    index = models.IntegerField(
        help_text='The index of the section in the resume. This number determines the position of the section in the resume. (0-based)')
    type = models.CharField(max_length=3, choices=ResumeSectionType.choices,
                            help_text='The type of the section. Can be Education, Experience, Skill, Strength, Project or Others.')

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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,
                          help_text='The unique identifier for the education entry.')
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text='The user who the education entry belongs to.')
    resume_section = models.OneToOneField(ResumeSection, on_delete=models.CASCADE,
                                          help_text='The resume section the education entry belongs to.')
    institution_name = models.CharField(max_length=250, help_text='The name of the institution the user studied at.')
    field_of_study = models.CharField(max_length=250, help_text='The field of study the user studied.')
    degree = models.CharField(max_length=250, null=True, blank=True,
                              help_text='The degree the user obtained. (optional)')
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True,
                                help_text='The country the institution is located in. (optional)')
    started_from_month = models.PositiveSmallIntegerField(null=True, blank=True,
                                                          help_text='The month the user started studying. (optional)')
    started_from_year = models.PositiveSmallIntegerField(null=True, blank=True,
                                                         help_text='The year the user started studying. (optional)')
    finished_at_month = models.PositiveSmallIntegerField(null=True, blank=True,
                                                         help_text='The month the user finished studying. (optional)')
    finished_at_year = models.PositiveSmallIntegerField(null=True, blank=True,
                                                        help_text='The year the user finished studying. (optional)')
    current = models.BooleanField(default=False, help_text='Whether the user is currently studying. default: False')
    description = models.TextField(max_length=3000, null=True, blank=True,
                                   help_text='The description of the education entry. User can provide any kind of description for that user. Usually in HTML format to support rich text. (optional)')  # TODO: May need to change the length
    created_at = models.DateTimeField(auto_now_add=True, help_text='The date and time the education entry was created.')
    updated_at = models.DateTimeField(auto_now=True,
                                      help_text='The date and time the education entry was last updated.')

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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,
                          help_text='The unique identifier for the experience entry.')
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text='The user who the experience entry belongs to.')
    resume_section = models.OneToOneField(ResumeSection, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=250, help_text='The name of the company the user worked at.')
    job_title = models.CharField(max_length=250, help_text='The title of the job the user had.')
    employment_type = models.CharField(max_length=3, choices=EmploymentType.choices,
                                       help_text='The type of employment the user had. Can be Full Time, Part Time, Contract, Internship, Freelance, Self Employed, Volunteer or Trainee.')
    city = models.CharField(max_length=50, blank=True, null=True,
                            help_text='The city the company is located in. (optional)')
    country = models.ForeignKey(Country, on_delete=models.CASCADE, blank=True, null=True,
                                help_text='The country the company is located in. (optional)')
    started_from_month = models.PositiveSmallIntegerField(null=True, blank=True,
                                                          help_text='The month the user started working.')
    started_from_year = models.PositiveSmallIntegerField(null=True, blank=True,
                                                         help_text='The year the user started working.')
    finished_at_month = models.PositiveSmallIntegerField(null=True, blank=True,
                                                         help_text='The month the user finished working. (optional)')
    finished_at_year = models.PositiveSmallIntegerField(null=True, blank=True,
                                                        help_text='The year the user finished working. (optional)')
    current = models.BooleanField(default=False, help_text='Whether the user is currently working. default: False')
    description = models.TextField(max_length=3000, null=True, blank=True,
                                   help_text='The description of the experience entry. User can provide any kind of description for that user. Usually in HTML format to support rich text. (optional)')  # TODO: May need to change the length
    created_at = models.DateTimeField(auto_now_add=True,
                                      help_text='The date and time the experience entry was created.')
    updated_at = models.DateTimeField(auto_now=True,
                                      help_text='The date and time the experience entry was last updated.')

    def __str__(self):
        return f'{self.company_name}'
