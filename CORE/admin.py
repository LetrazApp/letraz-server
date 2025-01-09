from django.contrib import admin

from .models import Waitlist, Country


# Register your models here.
@admin.register(Waitlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'referrer', 'waiting_number', 'created_at')
    list_filter = ('referrer',)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
