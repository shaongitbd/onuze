from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.UserViewSet, basename='users')
router.register('roles', views.RoleViewSet, basename='roles')
router.register('blocks', views.UserBlockViewSet, basename='blocks')

urlpatterns = [
    path('me/', views.CurrentUserView.as_view(), name='current-user'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password-change'),
]

urlpatterns += router.urls 