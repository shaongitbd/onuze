"""
URL Configuration for the Reddit Clone project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# API documentation setup
schema_view = get_schema_view(
    openapi.Info(
        title="Reddit Clone API",
        default_version='v1',
        description="API for Reddit Clone",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.IsAdminUser,),
)

# API URL patterns (v1)
api_v1_patterns = [
    # Include app-specific URL configurations
    path('users/', include('users.urls')),
    path('communities/', include('communities.urls')),
    path('posts/', include('posts.urls')),
    path('comments/', include('comments.urls')),
    path('votes/', include('votes.urls')),
    path('notifications/', include('notifications.urls')),
    path('moderation/', include('moderation.urls')),
    path('messages/', include('messaging.urls')),
    path('search/', include('search.urls')),
]

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # API routes
    path('api/v1/', include(api_v1_patterns)),
    
    # Authentication
    path('api/v1/auth/', include('djoser.urls')),
    path('api/v1/auth/', include('djoser.urls.jwt')),
    
    # API documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
