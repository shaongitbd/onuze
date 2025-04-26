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
    # Path-based URL for banning and unbanning users
    path('<str:path>/ban/<str:username>', views.BanByPathView.as_view(), name='community-ban-by-path'),
    path('<str:path>/unban/<str:username>', views.UnbanByPathView.as_view(), name='community-unban-by-path'),
    # Path-based URL for banned users
    path('<str:path>/banned/', views.BannedUsersView.as_view(), name='community-banned-users'),
    # Path-based URL for checking ban status
    path('<str:path>/ban-status/', views.BanStatusView.as_view(), name='community-ban-status'),
    # Path-based URL for checking if a specific user is banned
    path('<str:path>/users/<str:username>/ban-status/', views.UserBanStatusView.as_view(), name='user-ban-status'),
]

urlpatterns += router.urls 