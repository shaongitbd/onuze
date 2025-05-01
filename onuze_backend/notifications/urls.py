from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.NotificationViewSet, basename='notifications')

urlpatterns = [
    path('count/', views.NotificationCountView.as_view(), name='notification-count'),
    path('mark-all-read/', views.MarkAllReadView.as_view(), name='mark-all-read'),
]

urlpatterns += router.urls 