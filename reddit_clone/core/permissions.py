from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Assumes the model instance has an 'user' attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        # Ensure the object has a 'user' attribute.
        if not hasattr(obj, 'user'):
             # If the object doesn't have a user, deny permission for safety,
             # or adjust this logic based on your needs (e.g., allow admins).
             return False
             
        return obj.user == request.user 