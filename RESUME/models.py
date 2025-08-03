import uuid
from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator
from CORE.models import Country, Skill, Process
from PROFILE.models import User
from JOB.models import Job
from nanoid import generate as generate_nanoid
from letraz_server import settings


# Create your models here.
def generate_resume_id():
    nanoid = generate_nanoid()
    while Resume.objects.filter(id=f'job_{nanoid}'):
        nanoid = generate_nanoid()
    return f'rsm_{nanoid}'


class Resume(models.Model):
    class Status(models.TextChoices):
        Processing = 'P'
        Success = 'S'
        Failure = 'F'
        Manual = 'M'
        Other = 'O'
    id = models.CharField(max_length=25, primary_key=True, default=generate_resume_id, editable=False, help_text='The unique identifier for the resume entry.')
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text='The user who the resume belongs to.')
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, blank=True, null=True,
                            help_text='The job the resume is for. (optional in case it\'s a base resume for the user.)')
    base = models.BooleanField(default=False,
                               help_text='Whether the resume is a base resume for the user. One user can ')
    variations = models.ManyToManyField('Resume', related_name='related_resumes', blank=True)
    version = models.IntegerField(default=1, help_text='The version of the resume.')

    status = models.CharField(max_length=1, choices=Status.choices, null=True, blank=True, help_text='The status of the job as mentioned in the job posting. (optional)')
    process = models.ForeignKey(Process, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'job'], name="unique_resume_per_job",
                violation_error_message="This job is already have a resume.",
            ),
            models.UniqueConstraint(
                fields=['user', 'base'], condition=Q(base=True), name="unique_base_resume",
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

    def get_skill_resume_section(self):
        resume_skill_section_qs = self.resumesection_set.filter(
            type=ResumeSection.ResumeSectionType.Skill)
        if resume_skill_section_qs.exists():
            return resume_skill_section_qs.first()
        else:
            return self.create_section(ResumeSection.ResumeSectionType.Skill)

    def add_skill(self, skill_name, skill_category=None, skill_proficiency=None):
        skill: Skill
        skill, created = Skill.objects.get_or_create(name=skill_name, category=skill_category)
        resume_skill_section: ResumeSection = self.get_skill_resume_section()
        proficiency: Proficiency
        proficiency, created = resume_skill_section.proficiency_set.get_or_create(skill=skill)
        if skill_proficiency:
            if str(skill_proficiency) not in Proficiency.Level.values:
                raise ValueError('Invalid proficiency level.')
            proficiency.level = skill_proficiency
        else:
            proficiency.level = None
        proficiency.save()
        return proficiency

    def edit_skill(self, proficiency_id, skill_name, skill_category, skill_proficiency):
        resume_skill_section: ResumeSection = self.get_skill_resume_section()
        proficiency: Proficiency
        proficiency = resume_skill_section.proficiency_set.get(id=proficiency_id)
        category_of_skill = skill_category
        skill: Skill
        skill, created = Skill.objects.get_or_create(name=skill_name, category=category_of_skill)
        proficiency.skill = skill
        if skill_proficiency and skill_proficiency not in Proficiency.Level.values:
            raise ValueError(f'Invalid proficiency level: `{skill_proficiency}`')
        proficiency.level = skill_proficiency
        proficiency.save()
        return proficiency

    def remove_skill(self, proficiency_id):
        skill_resume_section: ResumeSection = self.get_skill_resume_section()
        proficiency: Proficiency
        for proficiency in skill_resume_section.proficiency_set.all():
            if str(proficiency.id) == str(proficiency_id):
                proficiency.delete()
                return True
        else:
            raise ValueError

    def __str__(self):
        return f'{"[Base] " if self.base else None}{self.id} [{self.user.get_full_name()}]'


class ResumeSection(models.Model):
    class ResumeSectionType(models.TextChoices):
        Education = 'edu'
        Experience = 'exp'
        Skill = 'skl'
        Project = 'prj'
        Certification = 'crt'
        Others = 'oth'

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4,
        editable=False, help_text='The unique identifier for the resume section entry.'
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
    started_from_month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], blank=True,
                                             null=True, help_text="Month when the education started (1-12).")
    started_from_year = models.IntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2100)], blank=True,
                                            null=True, help_text="Year when the education started (YYYY).")
    finished_at_month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], blank=True,
                                            null=True, help_text="Month when the education was completed (1-12).")
    finished_at_year = models.IntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2100)], blank=True,
                                           null=True, help_text="Year when the education was completed (YYYY).")
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
    started_from_month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], blank=True,
                                             null=True, help_text="Month when the experience started (1-12).")
    started_from_year = models.IntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2100)], blank=True,
                                            null=True, help_text="Year when the experience started (YYYY).")
    finished_at_month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], blank=True,
                                            null=True, help_text="Month when the experience was completed (1-12).")
    finished_at_year = models.IntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2100)], blank=True,
                                           null=True, help_text="Year when the experience was completed (YYYY).")
    current = models.BooleanField(default=False, help_text='Whether the user is currently working. default: False')
    description = models.TextField(max_length=3000, null=True, blank=True,
                                   help_text='The description of the experience entry. User can provide any kind of description for that user. Usually in HTML format to support rich text. (optional)')  # TODO: May need to change the length
    created_at = models.DateTimeField(auto_now_add=True,
                                      help_text='The date and time the experience entry was created.')
    updated_at = models.DateTimeField(auto_now=True,
                                      help_text='The date and time the experience entry was last updated.')

    def __str__(self):
        return f'{self.company_name}'


class Proficiency(models.Model):
    class Level(models.TextChoices):
        Beginner = 'BEG'
        Intermediate = 'INT'
        Advanced = 'ADV'
        Expert = 'EXP'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,
                          help_text='The unique identifier for the experience entry.')
    skill = models.ForeignKey(Skill, models.CASCADE, null=False, blank=False)
    resume_section = models.ForeignKey(ResumeSection, models.CASCADE, null=False, blank=False)
    level = models.CharField(max_length=3, choices=Level.choices, null=True)

    def __str__(self):
        return f'{self.skill.name} [{self.skill.category}] - {self.get_level_display()}'


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,
                          help_text="Unique identifier for the project")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             help_text="The user who owns this project")
    resume_section = models.OneToOneField(ResumeSection, on_delete=models.CASCADE)
    category = models.CharField(max_length=255, blank=True, null=True,
                                help_text="Category or type of the project (e.g., Web Development, Mobile App).")
    name = models.CharField(max_length=255, help_text="Name of the project.")
    description = models.TextField(blank=True, null=True,
                                   help_text="Detailed description of the project and its objectives.")
    skills_used = models.ManyToManyField(Skill, related_name='skills_used', blank=True,
                                         help_text="Technical skills and technologies used in this project.")
    role = models.CharField(max_length=255, blank=True, null=True,
                            help_text="Your role or position in this project (e.g., Lead Developer, UI Designer).")
    github_url = models.URLField(blank=True, null=True, help_text="Link to the project's GitHub repository.")
    live_url = models.URLField(blank=True, null=True, help_text="Link to the live/deployed version of the project.")
    started_from_month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], blank=True,
                                             null=True, help_text="Month when the project started (1-12).")
    started_from_year = models.IntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2100)], blank=True,
                                            null=True, help_text="Year when the project started (YYYY).")
    finished_at_month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], blank=True,
                                            null=True, help_text="Month when the project was completed (1-12).")
    finished_at_year = models.IntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2100)], blank=True,
                                           null=True, help_text="Year when the project was completed (YYYY).")
    current = models.BooleanField(blank=True, null=True, help_text="Indicates if this is a current/ongoing project.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the project was first created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the project was last updated.")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

    def add_skill(self, skill_name, skill_category=None):
        skill: Skill
        skill, created = Skill.objects.get_or_create(name=skill_name, category=skill_category)
        self.skills_used.add(skill)
        self.save()
        self.resume_section.resume.add_skill(skill_name, skill_category)
        return skill


class Certification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,
                          help_text="Unique identifier for the certification")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             help_text="The user who owns this certification")
    resume_section = models.OneToOneField(ResumeSection, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False, null=False, help_text="Name of the certification.")
    issuing_organization = models.CharField(max_length=255, blank=True, null=True)
    issue_date = models.DateField(blank=True, null=True, help_text="Date when the certification was issued.")
    credential_url = models.URLField(blank=True, null=True, help_text="Link to the certification credential.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the certification was first created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the certification was last updated.")

    class Meta:
        ordering = ['-created_at']
