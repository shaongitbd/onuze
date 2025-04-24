from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.PostViewSet, basename='posts')
router.register('media', views.PostMediaViewSet, basename='post-media')

# The router now handles the path-based detail URL for PostViewSet
urlpatterns = router.urls 