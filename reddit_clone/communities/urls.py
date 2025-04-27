from django.urls import path, include
# Use NestedSimpleRouter for handling nested resources
from rest_framework_nested.routers import DefaultRouter, NestedSimpleRouter 
from . import views

# Main router for top-level resources like communities
router = DefaultRouter()
router.register('', views.CommunityViewSet, basename='communities')

# Nested router for moderators under a specific community (using path)
# This will create URLs like /communities/{community_path}/moderators/
communities_router = NestedSimpleRouter(router, r'', lookup='community')
communities_router.register(r'moderators', views.CommunityModeratorViewSet, basename='community-moderators')
# Also nest members under the community path, using username as lookup
communities_router.register(r'members', views.CommunityMemberViewSet, basename='community-members') 
# Also nest rules under the community path
communities_router.register(r'rules', views.CommunityRuleViewSet, basename='community-rules') 


# --- Other Routers (Keep as is or adjust if needed) ---
# Router for rules (currently not nested under community path in ViewSet) - REMOVED
# rules_router = DefaultRouter() 
# rules_router.register('rules', views.CommunityRuleViewSet, basename='community-rules')

# Router for flairs (currently not nested under community path in ViewSet)
flairs_router = DefaultRouter()
flairs_router.register('flairs', views.FlairViewSet, basename='flairs')

# Router for members (using community ID - keep for now or change later) - REMOVED
# member_router = DefaultRouter()
# member_router.register('members', views.CommunityMemberViewSet, basename='members')


# --- URL Patterns ---
urlpatterns = [
    # Include the main router URLs (e.g., /communities/, /communities/{path}/)
    path('', include(router.urls)),
    
    # Include the nested moderator AND MEMBER router URLs 
    # (e.g., /communities/{community_path}/moderators/{pk}/, /communities/{community_path}/members/{pk or username}/)
    path('', include(communities_router.urls)),

    # Include other routers (can be adjusted later if nesting is desired)
    # path('', include(rules_router.urls)), # REMOVED
    path('', include(flairs_router.urls)),
    
    # UUID-based URL for member management (can be removed/changed later) - REMOVED
    # path('by-id/<uuid:community_id>/', include(member_router.urls)), 

    # Path-based URLs for specific views (keep these)
    # path('<str:path>/members/', views.CommunityMembersByPathView.as_view(), name='community-members-by-path'), # Replaced by nested router
    # path('<str:path>/moderators/', views.CommunityModeratorsByPathView.as_view(), name='community-moderators-by-path'), # Replaced by nested router
    path('<str:path>/ban/<str:username>', views.BanByPathView.as_view(), name='community-ban-by-path'),
    path('<str:path>/unban/<str:username>', views.UnbanByPathView.as_view(), name='community-unban-by-path'),
    path('<str:path>/banned/', views.BannedUsersView.as_view(), name='community-banned-users'),
    path('<str:path>/ban-status/', views.BanStatusView.as_view(), name='community-ban-status'),
    path('<str:path>/users/<str:username>/ban-status/', views.UserBanStatusView.as_view(), name='user-ban-status'),
]