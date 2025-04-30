"""
URL Configuration for the Secure Thread project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# API documentation setup
schema_view = get_schema_view(
    openapi.Info(
        title="Secure Thread API",
        default_version='v1',
        description="API for Secure Thread",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(AllowAny,),
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
    path('security/', include('security.urls')),
    path('uploads/', include('uploads.urls')),
]

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # API routes
    path('api/v1/', include(api_v1_patterns)),
    
    # Authentication - using both cookie-based and standard JWT auth
    path('api/v1/auth/', include('djoser.urls')),
    path('api/v1/auth/', include('djoser.urls.jwt')),  # Standard JWT auth (fallback)
    path('api/v1/auth/', include('security.urls')),    # Cookie-based JWT auth (recommended)
    
    # CAPTCHA URLs
    path('captcha/', include('captcha.urls')),
    
    # API documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
