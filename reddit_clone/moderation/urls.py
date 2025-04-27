from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('reports', views.ReportViewSet, basename='reports')
router.register('ban-appeals', views.BanAppealViewSet, basename='ban-appeals')

urlpatterns = [
    path('communities/<str:community_path>/reports/', views.CommunityReportListView.as_view(), name='community-reports-by-path'),
]

urlpatterns += router.urls 