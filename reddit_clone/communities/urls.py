from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.CommunityViewSet, basename='communities')
router.register('rules', views.CommunityRuleViewSet, basename='community-rules')
router.register('flairs', views.FlairViewSet, basename='flairs')

# Community member management routes
member_router = DefaultRouter()
member_router.register('members', views.CommunityMemberViewSet, basename='members')
member_router.register('moderators', views.CommunityModeratorViewSet, basename='moderators')

urlpatterns = [
    path('<uuid:community_id>/', include(member_router.urls)),
]

urlpatterns += router.urls 