from django.contrib import admin

from RESUME.models import Resume, Education, Experience, ResumeSection, Skill, Proficiency


# Register your models here.
@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'job', 'base')
    list_filter = ('base',)


# Register your models here.
@admin.register(ResumeSection)
class ResumeSectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'resume', 'index', 'type')
    list_filter = ('type',)


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'institution_name', 'field_of_study', 'degree')
    list_filter = ('current',)


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'company_name', 'job_title')
    list_filter = ('employment_type', 'current',)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'name')


@admin.register(Proficiency)
class ProficiencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'skill', 'resume_section', 'level')
    list_filter = ('level',)
