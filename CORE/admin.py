from django.contrib import admin

from .models import Waitlist, Country, Skill


# Register your models here.
@admin.register(Waitlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'referrer', 'waiting_number', 'has_access', 'created_at')
    list_filter = ('referrer', 'has_access')
    list_editable = ('has_access',)
    search_fields = ('email',)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'name')
