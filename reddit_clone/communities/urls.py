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
    # Path-based URL for community details
    path('<str:path>/', views.CommunityDetailByPathView.as_view(), name='community-detail-by-path'),
    # UUID-based URL for backward compatibility (can be removed later)
    path('by-id/<uuid:community_id>/', include(member_router.urls)),
    # Path-based URL for members and moderators
    path('<str:path>/members/', views.CommunityMembersByPathView.as_view(), name='community-members-by-path'),
    path('<str:path>/moderators/', views.CommunityModeratorsByPathView.as_view(), name='community-moderators-by-path'),
]

urlpatterns += router.urls 