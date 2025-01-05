from django.urls import path, include

urlpatterns = [
    path('', include('CORE.api_urls')),
]
