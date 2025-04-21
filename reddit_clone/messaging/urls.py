from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.PrivateMessageViewSet, basename='messages')

urlpatterns = [
    path('conversations/<uuid:user_id>/', views.ConversationView.as_view(), name='conversation'),
    path('unread-count/', views.UnreadCountView.as_view(), name='unread-count'),
]

urlpatterns += router.urls 