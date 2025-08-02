from django.contrib import admin
from django.utils.html import format_html

from RESUME.models import Resume, Education, Experience, ResumeSection, Proficiency, Project, Certification


# Register your models here.
@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'job', 'base')
    list_filter = ('base', 'status')


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


@admin.register(Proficiency)
class ProficiencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'skill', 'resume_section', 'level')
    search_fields = ('id', 'skill__name')
    list_filter = ('level',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'category')
    search_fields = (
        'name',
        'description',
        'category',
        'role',
        'user__username',
        'user__email'
    )

    autocomplete_fields = ['user']
    filter_horizontal = ('skills_used',)
    readonly_fields = ('created_at', 'updated_at', 'id')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'category', 'user', 'resume_section')
        }),
        ('Project Details', {
            'fields': ('role', 'skills_used', 'current')
        }),
        ('URLs', {
            'fields': ('github_url', 'live_url'),
            'classes': ('collapse',)
        }),
        ('Timeline', {
            'fields': (
                ('started_from_month', 'started_from_year'),
                ('finished_at_month', 'finished_at_year')
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def display_github_link(self, obj):
        if obj.github_url:
            return format_html('<a href="{}" target="_blank">GitHub Repository</a>', obj.github_url)
        return "-"

    display_github_link.short_description = "GitHub"

    def display_live_link(self, obj):
        if obj.live_url:
            return format_html('<a href="{}" target="_blank">Live Site</a>', obj.live_url)
        return "-"

    display_live_link.short_description = "Live URL"

    class Media:
        css = {
            'all': ('admin/css/widgets.css',)
        }
        js = ('admin/js/admin/RelatedObjectLookups.js',)



@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ['id']
