from django.urls import path
from . import admin_api_views

urlpatterns = [
    path('', admin_api_views.admin_waitlist_list),
    path('<uuid:waitlist_id>/', admin_api_views.admin_waitlist_update),
    path('bulk-update/', admin_api_views.admin_waitlist_bulk_update),
] 