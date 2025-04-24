from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.VoteViewSet, basename='votes')

urlpatterns = [
    # Path-based URLs for voting
    path('posts/<str:post_path>/vote/', views.PostVoteByPathView.as_view(), name='post-vote-by-path'),
    path('comments/<uuid:comment_id>/vote/', views.CommentVoteView.as_view(), name='comment-vote'),
    
    # Legacy ID-based URLs for backward compatibility (can be removed later)
    path('posts/by-id/<uuid:post_id>/vote/', views.PostVoteView.as_view(), name='post-vote'),
]

urlpatterns += router.urls 