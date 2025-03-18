from django.urls import path
from . import api_views

urlpatterns = [
    path('health/', api_views.health_check, name='health-check'),
    path('error-example/', api_views.error_example, name='error-example'),
    path('error-list-example/', api_views.error_list_example, name='error-list-example'),
    path('waitlist/', api_views.waitlist_crud, name='waitlist-crud'),
    path('skills/', api_views.get_all_skill, name='get-all-skill'),
]
