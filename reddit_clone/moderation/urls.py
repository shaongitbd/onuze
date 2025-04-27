from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet, BanAppealViewSet, CommunityReportListView, CommunityBanAppealListView, CommunityBanAppealDetailView

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'ban-appeals', BanAppealViewSet, basename='ban_appeal')

# Community-specific report and ban appeal paths
community_report_patterns = [
    # Report patterns
    path('communities/<str:community_path>/reports/', CommunityReportListView.as_view(), name='community_reports'),
    
    # Ban appeal list views
    path('communities/<str:community_path>/ban-appeals/', CommunityBanAppealListView.as_view(), name='community_ban_appeals'),
    path('communities/ban-appeals/', CommunityBanAppealListView.as_view(), name='community_ban_appeals_no_community'),
    
    # Ban appeal detail views - WITH community path
    path('communities/<str:community_path>/ban-appeals/<uuid:ban_appeal_id>/', 
         CommunityBanAppealDetailView.as_view({'get': 'retrieve'}), 
         name='community_ban_appeal_detail'),
    path('communities/<str:community_path>/ban-appeals/<uuid:ban_appeal_id>/approve/', 
         CommunityBanAppealDetailView.as_view({'post': 'approve'}), 
         name='community_ban_appeal_approve'),
    path('communities/<str:community_path>/ban-appeals/<uuid:ban_appeal_id>/reject/', 
         CommunityBanAppealDetailView.as_view({'post': 'reject'}), 
         name='community_ban_appeal_reject'),
    
    # Ban appeal detail views - WITHOUT community path
    path('communities/ban-appeals/<uuid:ban_appeal_id>/', 
         CommunityBanAppealDetailView.as_view({'get': 'retrieve'}), 
         name='community_ban_appeal_detail_no_community'),
    path('communities/ban-appeals/<uuid:ban_appeal_id>/approve/', 
         CommunityBanAppealDetailView.as_view({'post': 'approve'}), 
         name='community_ban_appeal_approve_no_community'),
    path('communities/ban-appeals/<uuid:ban_appeal_id>/reject/', 
         CommunityBanAppealDetailView.as_view({'post': 'reject'}), 
         name='community_ban_appeal_reject_no_community'),
]

# The API URLs are determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    *community_report_patterns
] 