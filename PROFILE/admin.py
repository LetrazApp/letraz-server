from django.contrib import admin
from PROFILE.models import User


# Register your models here.
@admin.register(User)
class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_full_name', 'email', 'city', 'nationality')

    def get_full_name(self, obj: User) -> str:
        return obj.get_full_name()

    get_full_name.short_description = 'Name'
