from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.PostViewSet, basename='posts')
# Optionally register PostMediaViewSet if needed for listing/deleting specific media
# If registered, it will be at /api/v1/posts/media/{media_id}/
# router.register('media', views.PostMediaViewSet, basename='post-media') 

urlpatterns = router.urls 

# If you need custom actions on PostMediaViewSet that aren't standard REST,
# you might need to add specific path() entries here or adjust the router. 