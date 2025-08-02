from django.contrib import admin
from JOB.models import Job


# Register your models here.
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'company_name', 'location')
    list_filter = ('status', )
