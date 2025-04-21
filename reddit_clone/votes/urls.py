from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.VoteViewSet, basename='votes')

urlpatterns = [
    path('posts/<uuid:post_id>/vote/', views.PostVoteView.as_view(), name='post-vote'),
    path('comments/<uuid:comment_id>/vote/', views.CommentVoteView.as_view(), name='comment-vote'),
]

urlpatterns += router.urls 