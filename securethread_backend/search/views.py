from django.db.models import Q, Value, CharField
from django.db.models.functions import Concat
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from posts.models import Post
from comments.models import Comment
from communities.models import Community
from users.models import User
from .models import SearchHistory
from .serializers import SearchResultSerializer, SearchHistorySerializer


class SearchView(generics.GenericAPIView):
    """
    API endpoint for searching across posts, comments, communities, and users.
    """
    serializer_class = SearchResultSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get(self, request):
        query = request.query_params.get('q', '')
        if not query or len(query) < 3:
            return Response({"error": "Query must be at least 3 characters."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get filter parameters
        content_type = request.query_params.get('type', 'all')  # all, posts, comments, communities, users
        community_id = request.query_params.get('community', None)
        sort = request.query_params.get('sort', 'relevant')  # relevant, new, top
        
        # Initialize search query for PostgreSQL search
        search_query = SearchQuery(query)
        
        # Search posts
        if content_type in ['all', 'posts']:
            posts_query = Post.objects.filter(is_deleted=False)
            
            if community_id:
                posts_query = posts_query.filter(community__id=community_id)
            
            # Use PostgreSQL full-text search
            post_search_vector = SearchVector('title', weight='A') + SearchVector('content', weight='B')
            
            posts = posts_query.annotate(
                rank=SearchRank(post_search_vector, search_query)
            ).filter(rank__gt=0.1)
            
            # Apply sorting
            if sort == 'new':
                posts = posts.order_by('-created_at')
            elif sort == 'top':
                posts = posts.order_by('-upvote_count')
            else:  # relevant
                posts = posts.order_by('-rank')
        else:
            posts = Post.objects.none()
        
        # Search comments
        if content_type in ['all', 'comments']:
            comments_query = Comment.objects.filter(is_deleted=False)
            
            if community_id:
                comments_query = comments_query.filter(post__community__id=community_id)
            
            # Use PostgreSQL full-text search
            comment_search_vector = SearchVector('content', weight='A')
            
            comments = comments_query.annotate(
                rank=SearchRank(comment_search_vector, search_query)
            ).filter(rank__gt=0.1)
            
            # Apply sorting
            if sort == 'new':
                comments = comments.order_by('-created_at')
            elif sort == 'top':
                comments = comments.order_by('-upvote_count')
            else:  # relevant
                comments = comments.order_by('-rank')
        else:
            comments = Comment.objects.none()
        
        # Search communities
        if content_type in ['all', 'communities']:
            community_search_vector = SearchVector('name', weight='A') + SearchVector('description', weight='B')
            
            communities = Community.objects.annotate(
                rank=SearchRank(community_search_vector, search_query)
            ).filter(rank__gt=0.1)
            
            # Apply sorting
            if sort == 'new':
                communities = communities.order_by('-created_at')
            elif sort == 'top':
                communities = communities.order_by('-member_count')
            else:  # relevant
                communities = communities.order_by('-rank')
        else:
            communities = Community.objects.none()
        
        # Search users
        if content_type in ['all', 'users']:
            # For users, use simple contains since usernames don't need full-text search
            users = User.objects.filter(
                Q(username__icontains=query) | Q(bio__icontains=query)
            ).filter(is_active=True)
            
            # Apply sorting
            if sort == 'new':
                users = users.order_by('-date_joined')
            elif sort == 'top':
                users = users.order_by('-karma')
            else:  # relevant
                # For relevance sorting, prioritize username matches over bio matches
                users = users.annotate(
                    name_match=Value(1, output_field=CharField()) if Q(username__icontains=query) else Value(0, output_field=CharField())
                ).order_by('-name_match', '-karma')
        else:
            users = User.objects.none()
        
        # Calculate total results
        total_results = posts.count() + comments.count() + communities.count() + users.count()
        
        # Paginate results
        posts = posts[:10]
        comments = comments[:10]
        communities = communities[:5]
        users = users[:5]
        
        # Log the search if user is authenticated
        if request.user.is_authenticated:
            SearchHistory.objects.create(
                user=request.user,
                query=query,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                result_count=total_results
            )
        
        # Return serialized results
        serializer = self.get_serializer({
            'posts': posts,
            'comments': comments,
            'communities': communities,
            'users': users,
            'total_results': total_results,
            'query': query
        })
        
        return Response(serializer.data)
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SearchHistoryView(generics.ListAPIView):
    """
    API endpoint for viewing user's search history.
    """
    serializer_class = SearchHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SearchHistory.objects.filter(user=self.request.user).order_by('-created_at') 