from django.urls import path
from .views import CookieTokenObtainPairView, CookieTokenRefreshView, CookieTokenLogoutView
 
urlpatterns = [
    path('token/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', CookieTokenLogoutView.as_view(), name='token_logout'),
] 