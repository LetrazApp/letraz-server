from django.contrib import admin
from PROFILE.models import UserInfo


# Register your models here.
@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_full_name', 'email', 'city', 'nationality')

    def get_full_name(self, obj: UserInfo) -> str:
        return obj.get_full_name()

    get_full_name.short_description = 'Name'
