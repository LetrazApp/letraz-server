from django.urls import path, include

urlpatterns = [
    path('waitlist/', include('CORE.admin_api_urls')),
    # Add other admin API modules here as they are created
    # path('users/', include('PROFILE.admin_api_urls')),
    # path('jobs/', include('JOB.admin_api_urls')),
    # path('resumes/', include('RESUME.admin_api_urls')),
] 