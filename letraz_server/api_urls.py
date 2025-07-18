from django.urls import path, include

urlpatterns = [
    path('', include('CORE.api_urls')),
    path('job/', include('JOB.api_urls')),
    path('user/', include('PROFILE.api_urls')),
    path('resume/', include('RESUME.api_urls')),
    path('admin/', include('letraz_server.admin_api_urls')),
]
