from django.urls import path, include

urlpatterns = [
    path('', include('CORE.api_urls')),
    path('job/', include('JOB.api_urls')),
    path('user/', include('PROFILE.api_urls')),
    path('user/<str:user_id>/resume/', include('RESUME.api_urls')),
]
