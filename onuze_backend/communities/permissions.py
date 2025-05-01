from rest_framework import permissions


class IsCommunityOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a community to edit it.
    """
    
    def has_permission(self, request, view):
        # Allow all read-only requests
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to authenticated users
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Allow read-only requests
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if the community has a community_moderator with the current user as owner
        if hasattr(obj, 'moderators'):
            return obj.moderators.filter(user=request.user, is_owner=True).exists()
        
        # If the object is a moderator, check if the user is the owner of the community
        if hasattr(obj, 'community') and hasattr(obj.community, 'moderators'):
            return obj.community.moderators.filter(user=request.user, is_owner=True).exists()
        
        return False


class IsCommunityModeratorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow moderators of a community to edit it.
    """
    
    def has_permission(self, request, view):
        # Allow all read-only requests
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to authenticated users
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Allow read-only requests
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Get the community from the object
        community = None
        
        # If the object is a community, use it directly
        if hasattr(obj, 'moderators'):
            community = obj
        # If the object has a community attribute, use that
        elif hasattr(obj, 'community'):
            community = obj.community
        
        # If we couldn't determine the community, deny permission
        if community is None:
            return False
        
        # Check if the user is a moderator or owner of the community
        return community.moderators.filter(user=request.user).exists() 