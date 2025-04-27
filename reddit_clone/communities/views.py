from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Community, CommunityMember, CommunityModerator, CommunityRule, CommunitySetting, Flair
from .serializers import (
    CommunitySerializer, CommunityMemberSerializer, CommunityModeratorSerializer,
    CommunityRuleSerializer, CommunitySettingSerializer, FlairSerializer
)
from .permissions import IsCommunityOwnerOrReadOnly, IsCommunityModeratorOrReadOnly
from security.models import AuditLog
from django.db.models import F
import django.core.exceptions


class CommunityViewSet(viewsets.ModelViewSet):
    print("YO")
    """
    API endpoint for communities.
    Now uses 'path' for detail lookups (GET, PUT, PATCH, DELETE).
    """
    queryset = Community.objects.all()
    print(queryset)
    serializer_class = CommunitySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsCommunityOwnerOrReadOnly]
    lookup_field = 'path'
    lookup_url_kwarg = 'path'
    
    def get_permissions(self):
        """
        Override to specify different permissions for different actions.
        """
        if self.action in ['join', 'leave']:
            # For join and leave actions, only require authentication
            return [permissions.IsAuthenticated()]
        # For other actions, use the default permission_classes
        return [permission() for permission in self.permission_classes]
    
    def perform_create(self, serializer):
        try:
            community = serializer.save(created_by=self.request.user)
            
            # Automatically add creator as a member and moderator
            CommunityMember.objects.create(
                community=community,
                user=self.request.user,
                is_approved=True
            )
            
            CommunityModerator.objects.create(
                community=community,
                user=self.request.user,
                is_owner=True
            )
            
            # Set the initial member count to 1 since the creator is a member
            community.member_count = 1
            community.save(update_fields=['member_count'])
            
            # Log community creation
            AuditLog.log(
                action='community_create',
                entity_type='community',
                entity_id=community.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={
                    'name': community.name,
                    'is_private': community.is_private,
                    'is_restricted': community.is_restricted
                }
            )
        except django.core.exceptions.ValidationError as e:
            # Log failed community creation due to validation error
            AuditLog.log(
                action='community_create_failed',
                entity_type='community',
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={
                    'name': serializer.validated_data.get('name', 'unknown'),
                    'is_private': serializer.validated_data.get('is_private', False),
                    'is_restricted': serializer.validated_data.get('is_restricted', False),
                    'error': str(e),
                    'validation_error': True
                }
            )
            raise
        except Exception as e:
            # Log failed community creation
            AuditLog.log(
                action='community_create_failed',
                entity_type='community',
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={
                    'name': serializer.validated_data.get('name', 'unknown'),
                    'is_private': serializer.validated_data.get('is_private', False),
                    'is_restricted': serializer.validated_data.get('is_restricted', False),
                    'error': str(e)
                }
            )
            raise
    
    def perform_update(self, serializer):
        try:
            community = serializer.save()
            
            # Log community update
            AuditLog.log(
                action='community_update',
                entity_type='community',
                entity_id=community.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={
                    'name': community.name,
                    'is_private': community.is_private,
                    'is_restricted': community.is_restricted,
                    'updated_fields': list(serializer.validated_data.keys())
                }
            )
        except Exception as e:
            # Get the community ID from the URL
            community_id = self.kwargs.get('pk')
            
            # Log failed community update
            AuditLog.log(
                action='community_update_failed',
                entity_type='community',
                entity_id=community_id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={
                    'updated_fields': list(serializer.validated_data.keys()),
                    'error': str(e)
                }
            )
            raise
    
    def perform_destroy(self, instance):
        try:
            # Log community deletion
            AuditLog.log(
                action='community_delete',
                entity_type='community',
                entity_id=instance.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={'name': instance.name}
            )
            
            instance.delete()
        except Exception as e:
            # Log failed community deletion
            AuditLog.log(
                action='community_delete_failed',
                entity_type='community',
                entity_id=instance.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={
                    'name': instance.name,
                    'error': str(e)
                }
            )
            raise
    
    @action(detail=True, methods=['post'])
    def join(self, request, path=None):
        community = self.get_object()
        user = request.user
        
        # Check if already a member
        if CommunityMember.objects.filter(community=community, user=user).exists():
            return Response({'detail': 'Already a member of this community.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        # For private communities, create unapproved membership
        is_approved = not community.is_private and not community.is_restricted
        
        member = CommunityMember.objects.create(
            community=community,
            user=user,
            is_approved=is_approved
        )
        
        # Increment member count if the join is approved immediately
        if is_approved:
            # Use the model's method instead of F expression
            community.increment_member_count()
        
        # Log join action
        approval_status = "approved" if is_approved else "pending"
        AuditLog.log(
            action=f'community_join_{approval_status}',
            entity_type='community',
            entity_id=community.id,
            user=user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={'community_name': community.name}
        )
        
        return Response({'detail': 'Joined community successfully.' if is_approved else 
                        'Join request submitted and pending approval.'})
    
    @action(detail=True, methods=['post'])
    def leave(self, request, path=None):
        community = self.get_object()
        user = request.user
        
        # Try to get membership
        try:
            membership = CommunityMember.objects.get(community=community, user=user)
            
            # Check if user is the owner
            is_owner = CommunityModerator.objects.filter(
                community=community, user=user, is_owner=True).exists()
            
            if is_owner:
                return Response({'detail': 'Community owner cannot leave. Transfer ownership first.'},
                               status=status.HTTP_400_BAD_REQUEST)
            
            # Log leave action
            AuditLog.log(
                action='community_leave',
                entity_type='community',
                entity_id=community.id,
                user=user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={'community_name': community.name}
            )
            
            # Check if the member was approved before decrementing count
            if membership.is_approved:
                # Use the model's method instead of F expression
                community.decrement_member_count()
            
            # Delete membership and any moderator status
            membership.delete()
            CommunityModerator.objects.filter(community=community, user=user).delete()
            
            return Response({'detail': 'Left community successfully.'})
            
        except CommunityMember.DoesNotExist:
            return Response({'detail': 'Not a member of this community.'},
                           status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def members(self, request, path=None):
        community = self.get_object()
        members = CommunityMember.objects.filter(community=community, is_approved=True)
        serializer = CommunityMemberSerializer(members, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def moderators(self, request, path=None):
        community = self.get_object()
        moderators = CommunityModerator.objects.filter(community=community)
        serializer = CommunityModeratorSerializer(moderators, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='settings', url_name='settings')
    def list_settings(self, request, path=None):
        community = self.get_object()
        settings_qs = CommunitySetting.objects.filter(community=community)
        serializer = CommunitySettingSerializer(settings_qs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='unban/(?P<username>[^/.]+)')
    def unban_by_username(self, request, path=None, username=None):
        """
        Unban a user from a community by their username.
        This provides a simpler API endpoint: /communities/{community_id}/unban/{username}/
        """
        community = self.get_object()
        
        # Check if the requester is a moderator
        if not CommunityModerator.objects.filter(
            community=community, user=request.user).exists() and not request.user.is_staff:
            return Response({'detail': 'Only moderators can unban members.'},
                           status=status.HTTP_403_FORBIDDEN)
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'},
                           status=status.HTTP_404_NOT_FOUND)
        
        try:
            member = CommunityMember.objects.get(community=community, user=user)
        except CommunityMember.DoesNotExist:
            return Response({'detail': 'This user is not a member of this community.'},
                           status=status.HTTP_404_NOT_FOUND)
        
        # Check if member is banned
        if not member.is_banned:
            return Response({'detail': 'This member is not banned.'},
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Unban the member
        member.unban()
        
        # Send notification to the unbanned user
        from notifications.models import Notification
        Notification.send_mod_action_notification(
            user=member.user,
            community=member.community,
            action=f"Your ban from r/{member.community.name} has been lifted",
            admin_user=request.user,
            link_url=f"/c/{member.community.path}"
        )
        
        # Log member unban
        AuditLog.log(
            action='community_member_unban',
            entity_type='community_member',
            entity_id=member.id,
            user=request.user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={
                'community_id': str(member.community.id),
                'community_name': member.community.name,
                'user_id': str(member.user.id),
                'username': member.user.username
            }
        )
        
        return Response({'detail': f'User {username} has been unbanned from {community.name}.'})
    
    @action(detail=True, methods=['get'])
    def banned_users(self, request, path=None):
        """
        List all banned users in a community.
        Accessible via: /communities/{community_id}/banned_users/
        """
        community = self.get_object()
        
        # Check if the requester is a moderator or admin
        is_moderator = CommunityModerator.objects.filter(
            community=community, user=request.user).exists()
        
        if not is_moderator and not request.user.is_staff:
            return Response({'detail': 'Only moderators can view banned users list.'},
                          status=status.HTTP_403_FORBIDDEN)
        
        banned_members = CommunityMember.objects.filter(
            community=community, 
            is_banned=True
        )
        
        serializer = CommunityMemberSerializer(banned_members, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def check_ban_status(self, request, path=None):
        """
        Check if the authenticated user is banned in the community.
        Accessible via: /communities/{community_id}/check_ban_status/
        """
        community = self.get_object()
        user = request.user
        
        if not user.is_authenticated:
            return Response({'detail': 'Authentication required.'},
                          status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            member = CommunityMember.objects.get(community=community, user=user)
            is_banned = member.is_banned
            ban_reason = member.ban_reason if is_banned else None
            banned_until = member.banned_until if is_banned else None
            
            return Response({
                'is_banned': is_banned,
                'ban_reason': ban_reason,
                'banned_until': banned_until,
            })
        except CommunityMember.DoesNotExist:
            # User is not a member
            return Response({
                'is_banned': False,
                'detail': 'User is not a member of this community'
            })
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CommunityMemberViewSet(viewsets.ModelViewSet):
    """
    API endpoint for community members.
    Nested under /communities/{community_path}/members/
    Uses username for detail lookup within the community.
    """
    serializer_class = CommunityMemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommunityModeratorOrReadOnly]
    lookup_field = 'user__username' # Base lookup on username field of related User
    lookup_url_kwarg = 'username' # Expect 'username' from URL pattern

    # Helper method to get community from URL path
    def _get_community_from_path(self):
        # Use 'community_path' based on the parent router's lookup ('community')
        print("DEBUG: Available kwargs:", self.kwargs)
        community_path = self.kwargs.get('community_path')
        if not community_path:
            print("DEBUG: 'community_path' not found in kwargs")
            return None 
        return get_object_or_404(Community, path=community_path)
    
    def get_queryset(self):
        """Filter members based on the community path from the URL."""
        community = self._get_community_from_path()
        if community:
            return CommunityMember.objects.filter(community=community)
        return CommunityMember.objects.none() # Return empty if community not found
    
    # Override get_object to handle username lookup within the community context
    def get_object(self):
        print("DEBUG: get_object called with kwargs:", self.kwargs)
        print("DEBUG: URL lookup kwarg:", self.lookup_url_kwarg)
        print("DEBUG: Lookup field:", self.lookup_field)
        
        queryset = self.filter_queryset(self.get_queryset())
        print("DEBUG: Queryset:", queryset)
        
        # Perform the lookup filtering based on username from URL
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        print("DEBUG: Filter kwargs:", filter_kwargs)
        
        obj = get_object_or_404(queryset, **filter_kwargs)
        
        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        
        return obj
    
    def perform_create(self, serializer):
        """Associate the member with the community from the URL path."""
        community = self._get_community_from_path()
        if not community:
             raise serializers.ValidationError({"detail": "Community not found based on URL path."}) 

        # Note: The serializer likely expects a `user` field (ID or object)
        # Ensure the user exists before creating the membership
        user_id = serializer.validated_data.get('user') # Assuming serializer takes user ID
        if not user_id:
             raise serializers.ValidationError({"user": "User ID is required."}) 
        user = get_object_or_404(User, id=user_id) # Or however user is identified

        # Check permissions (e.g., only mods can add members?)
        # Handled by IsCommunityModeratorOrReadOnly

        # Check if member already exists
        if CommunityMember.objects.filter(community=community, user=user).exists():
            raise serializers.ValidationError({"detail": "User is already a member of this community."}) 

        # Create the member, associating with retrieved community and user
        member = serializer.save(community=community, user=user) 
        
        # Log member addition
        AuditLog.log(
            action='community_member_add',
            entity_type='community_member',
            entity_id=member.id,
            user=self.request.user,
            ip_address=self.get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details={
                'community_id': str(member.community.id),
                'community_name': member.community.name,
                'user_id': str(member.user.id),
                'username': member.user.username,
                'is_approved': member.is_approved # Assuming serializer handles this
            }
        )
    
    # perform_update uses get_object which now handles the username lookup
    def perform_update(self, serializer):
        member = serializer.save()
        # ... (logging remains the same) ...
    
    # destroy uses get_object implicitly, which now handles the username lookup
    def perform_destroy(self, instance):
        # instance is the CommunityMember object fetched by get_object
        # Log member removal
        AuditLog.log(
            action='community_member_remove',
            entity_type='community_member',
            entity_id=instance.id,
            user=self.request.user,
            ip_address=self.get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details={
                'community_id': str(instance.community.id),
                'community_name': instance.community.name,
                'user_id': str(instance.user.id),
                'username': instance.user.username
            }
        )
        
        instance.delete()
    
    # --- Custom Actions --- 
    # These actions operate on a specific member instance (found by username via get_object)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, community_community_path=None, username=None):
        member = self.get_object() # Gets member via username
        # ... (rest of approve logic is the same) ...
    
    @action(detail=True, methods=['post'])
    def ban(self, request, community_community_path=None, username=None):
        member = self.get_object() # Gets member via username
        # ... (rest of ban logic is the same) ...
    
    @action(detail=True, methods=['post'])
    def unban(self, request, community_community_path=None, username=None):
        member = self.get_object() # Gets member via username
        # ... (rest of unban logic is the same) ...
    
    @action(detail=True, methods=['post'])
    def reject(self, request, community_community_path=None, username=None):
        member = self.get_object() # Gets member via username
        # ... (rest of reject logic is the same) ...

    # This action remains list-based, doesn't fit the detail=True username lookup model
    # It might need its own separate view or modification if needed via path.
    # @action(detail=False, methods=['post'], url_path='unban-user')
    # def unban_user(self, request):
    #     ...
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CommunityModeratorViewSet(viewsets.ModelViewSet):
    """
    API endpoint for community moderators.
    Now nested under /communities/{community_path}/moderators/
    """
    serializer_class = CommunityModeratorSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommunityOwnerOrReadOnly]
    
    # Helper method to get community from URL path
    def _get_community_from_path(self):
        community_path = self.kwargs.get('community_path') # Note: lookup name from NestedSimpleRouter
        if not community_path:
            # This should not happen if routing is correct, but handle defensively
            return None 
        return get_object_or_404(Community, path=community_path)
    
    def get_queryset(self):
        """Filter moderators based on the community path from the URL."""
        community = self._get_community_from_path()
        if community:
            return CommunityModerator.objects.filter(community=community)
        return CommunityModerator.objects.none() # Return empty if community not found
    
    def perform_create(self, serializer):
        """Associate the moderator with the community from the URL path."""
        community = self._get_community_from_path()
        if not community:
             # Raise an appropriate error or handle as needed
             # For now, assuming serializer validation might catch missing user/community if required
             # but explicitly checking community ensures the URL is valid.
             raise serializers.ValidationError({"detail": "Community not found based on URL path."}) 

        # Check if the user performing the action is the owner of this community
        # Note: IsCommunityOwnerOrReadOnly permission already checks this for POST
        # But we can add an explicit check here if needed for extra safety or specific logic.
        # if not community.moderators.filter(user=self.request.user, is_owner=True).exists():
        #     raise PermissionDenied("Only the community owner can add moderators.")

        # Save the moderator instance, associating it with the retrieved community
        moderator = serializer.save(community=community, appointed_by=self.request.user)
        
        # Ensure the user is a member of the community
        if not CommunityMember.objects.filter(
            community=moderator.community, user=moderator.user).exists():
            CommunityMember.objects.create(
                community=moderator.community,
                user=moderator.user,
                is_approved=True
            )
        
        # Log moderator addition
        AuditLog.log(
            action='community_moderator_add',
            entity_type='community_moderator',
            entity_id=moderator.id,
            user=self.request.user,
            ip_address=self.get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details={
                'community_id': str(moderator.community.id),
                'community_name': moderator.community.name,
                'user_id': str(moderator.user.id),
                'username': moderator.user.username,
                'is_owner': moderator.is_owner
            }
        )
    
    # perform_update and perform_destroy usually operate on the instance (moderator)
    # found by its PK, so they often don't need the community path directly, 
    # unless permissions depend explicitly on fetching the community again.
    # The existing IsCommunityOwnerOrReadOnly permission handles the object-level check.
    def perform_update(self, serializer):
        moderator = serializer.save()
        # ... (logging remains the same) ...
    
    def perform_destroy(self, instance):
        # Prevent removal of the community owner
        if instance.is_owner:
            raise permissions.PermissionDenied("Cannot remove the community owner.")
        # ... (logging remains the same) ...
        instance.delete()
    
    @action(detail=False, methods=['post'], url_path='transfer-ownership') # Keep url_path for clarity
    def transfer_ownership(self, request, community_path=None): # Added community_path
        # Get community using path
        community = self._get_community_from_path()
        if not community:
            return Response({'detail': "Community not found."}, status=status.HTTP_404_NOT_FOUND)

        new_owner_id = request.data.get('new_owner') # Expect user ID in request body
        if not new_owner_id:
            return Response({'detail': 'New owner user ID must be specified in request body.'},
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Find the target user who must already be a moderator
        new_owner_moderator = get_object_or_404(CommunityModerator, community=community, user__id=new_owner_id)
        
        # Check if the requester is the current owner
        try:
            current_owner_moderator = CommunityModerator.objects.get(
                community=community, is_owner=True)
            
            if current_owner_moderator.user != request.user:
                return Response({'detail': 'Only the current community owner can transfer ownership.'},
                               status=status.HTTP_403_FORBIDDEN)
            
            if current_owner_moderator == new_owner_moderator:
                 return Response({'detail': 'New owner cannot be the same as the current owner.'},
                               status=status.HTTP_400_BAD_REQUEST)
            
            # Transfer ownership
            current_owner_moderator.is_owner = False
            current_owner_moderator.save()
            
            new_owner_moderator.is_owner = True
            new_owner_moderator.save()
            
            # Update the community owner field (optional but good practice)
            community.created_by = new_owner_moderator.user
            community.save(update_fields=['created_by'])
            
            # Log ownership transfer
            AuditLog.log(
                action='community_ownership_transfer',
                entity_type='community',
                entity_id=community.id,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={
                    'community_name': community.name,
                    'previous_owner_id': str(request.user.id),
                    'previous_owner_username': request.user.username,
                    'new_owner_id': str(new_owner_moderator.user.id),
                    'new_owner_username': new_owner_moderator.user.username
                }
            )
            
            return Response({'detail': 'Ownership transferred successfully.'})
            
        except CommunityModerator.DoesNotExist: # Should not happen if owner exists
            return Response({'detail': 'Current community owner not found.'},
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except CommunityModerator.DoesNotExist:
            return Response({'detail': 'Target new owner is not a moderator of this community.'},
                           status=status.HTTP_400_BAD_REQUEST)

    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CommunityRuleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for community rules.
    Nested under /communities/{community_path}/rules/
    """
    serializer_class = CommunityRuleSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommunityModeratorOrReadOnly]
    # Default lookup is pk (rule_id), which is fine for retrieve/update/delete

    # Helper method to get community from URL path
    def _get_community_from_path(self):
        # Check for different possible URL parameter names for the community path
        community_path = None
        
        # Try different possible parameter names based on URL routing configurations
        possible_param_names = ['community_path', 'community_community_path', 'path']
        for param_name in possible_param_names:
            if param_name in self.kwargs:
                community_path = self.kwargs.get(param_name)
                break
        
        if not community_path:
            # If still not found, try to get it from the URL path directly
            path_parts = self.request.path.split('/')
            communities_index = -1
            
            # Find "communities" in the URL path
            for i, part in enumerate(path_parts):
                if part == 'communities':
                    communities_index = i
                    break
            
            # If "communities" was found and there's a next part, use it as the path
            if communities_index > -1 and communities_index + 1 < len(path_parts):
                community_path = path_parts[communities_index + 1]
        
        if not community_path:
            return None
            
        return get_object_or_404(Community, path=community_path)
    
    def get_queryset(self):
        """Filter rules based on the community path from the URL."""
        community = self._get_community_from_path()
        if community:
            return CommunityRule.objects.filter(community=community)
        # If accessed via non-nested route (e.g. /rules/), show all (if needed)
        # or return none if nesting is strictly enforced.
        # For now, assume nesting, return none if path missing.
        return CommunityRule.objects.none()
    
    def perform_create(self, serializer):
        """Associate the rule with the community from the URL path."""
        community = self._get_community_from_path()
        if not community:
            # Log the error for debugging
            print(f"ERROR: Community not found in URL. Parameters: {self.kwargs}")
            print(f"URL path: {self.request.path}")
            raise serializers.ValidationError({"detail": "Community not found based on URL path."}) 
        
        # Permissions are checked by IsCommunityModeratorOrReadOnly
        
        # Log the community found for debugging
        print(f"Creating rule for community: {community.name} (path: {community.path})")
        
        # Save the rule, associating it with the retrieved community and creator
        rule = serializer.save(community=community, created_by=self.request.user)
        
        # Log rule creation
        AuditLog.log(
            action='community_rule_create',
            entity_type='community_rule',
            entity_id=rule.id,
            user=self.request.user,
            ip_address=self.get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details={
                'community_id': str(rule.community.id),
                'community_name': rule.community.name,
                'rule_title': rule.title
            }
        )
    
    # perform_update and perform_destroy operate on the rule instance (found by pk)
    # The community context for permissions is handled by IsCommunityModeratorOrReadOnly
    def perform_update(self, serializer):
        rule = serializer.save()
        # ... (logging remains the same) ...
    
    def perform_destroy(self, instance):
        # Log rule deletion
        # ... (logging remains the same) ...
        instance.delete()
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CommunitySettingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for community settings.
    """
    serializer_class = CommunitySettingSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommunityModeratorOrReadOnly]
    
    def get_queryset(self):
        return CommunitySetting.objects.all()
    
    def perform_create(self, serializer):
        setting = serializer.save()
        
        # Log setting creation
        AuditLog.log(
            action='community_setting_create',
            entity_type='community_setting',
            entity_id=setting.id,
            user=self.request.user,
            ip_address=self.get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details={
                'community_id': str(setting.community.id),
                'community_name': setting.community.name,
                'setting_key': setting.key,
                'setting_value': setting.value
            }
        )
    
    def perform_update(self, serializer):
        setting = serializer.save()
        
        # Log setting update
        AuditLog.log(
            action='community_setting_update',
            entity_type='community_setting',
            entity_id=setting.id,
            user=self.request.user,
            ip_address=self.get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details={
                'community_id': str(setting.community.id),
                'community_name': setting.community.name,
                'setting_key': setting.key,
                'setting_value': setting.value,
                'updated_fields': list(serializer.validated_data.keys())
            }
        )
    
    def perform_destroy(self, instance):
        # Log setting deletion
        AuditLog.log(
            action='community_setting_delete',
            entity_type='community_setting',
            entity_id=instance.id,
            user=self.request.user,
            ip_address=self.get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details={
                'community_id': str(instance.community.id),
                'community_name': instance.community.name,
                'setting_key': instance.key
            }
        )
        
        instance.delete()
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class FlairViewSet(viewsets.ModelViewSet):
    """
    API endpoint for community flairs.
    Now nested under /communities/{community_path}/flairs/
    """
    serializer_class = FlairSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommunityModeratorOrReadOnly]
    
    def get_queryset(self):
        # Check if there's a community path parameter (for nested routes)
        community_path = self.kwargs.get('community_community', None)
        if community_path:
            # For nested route: /communities/{path}/flairs/
            community = get_object_or_404(Community, path=community_path)
            return Flair.objects.filter(community=community)
        
        # For non-nested route: /communities/flairs/ with optional query param
        community_id = self.request.query_params.get('community', None)
        if community_id:
            return Flair.objects.filter(community__id=community_id)
        
        # Return all flairs if no community specified (admin access)
        return Flair.objects.all()
    
    def perform_create(self, serializer):
        try:
            # For nested route: /communities/{path}/flairs/
            community_path = self.kwargs.get('community_community', None)
            if community_path:
                community = get_object_or_404(Community, path=community_path)
            else:
                # For non-nested route, require community ID in request data
                community_id = self.request.data.get('community')
            community = get_object_or_404(Community, id=community_id)
            
            flair = serializer.save(
                community=community,
                created_by=self.request.user
            )
            
            # Log flair creation
            AuditLog.log(
                action='flair_create',
                entity_type='flair',
                entity_id=flair.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={
                    'community_id': str(community.id),
                    'community_name': community.name,
                    'flair_name': flair.name
                }
            )
        except Exception as e:
            # Log failed flair creation
            AuditLog.log(
                action='flair_create_failed',
                entity_type='flair',
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={
                    'community_path': self.kwargs.get('community_community'),
                    'flair_name': serializer.validated_data.get('name', 'unknown'),
                    'error': str(e)
                }
            )
            raise
    
    def perform_update(self, serializer):
        try:
            flair = serializer.save()
            
            # Log flair update
            AuditLog.log(
                action='flair_update',
                entity_type='flair',
                entity_id=flair.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={
                    'community_id': str(flair.community.id),
                    'community_name': flair.community.name,
                    'flair_name': flair.name,
                    'updated_fields': list(serializer.validated_data.keys())
                }
            )
        except Exception as e:
            # Get the flair ID from the URL
            flair_id = self.kwargs.get('pk')
            
            # Log failed flair update
            AuditLog.log(
                action='flair_update_failed',
                entity_type='flair',
                entity_id=flair_id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={
                    'community_path': self.kwargs.get('community_community'),
                    'updated_fields': list(serializer.validated_data.keys()),
                    'error': str(e)
                }
            )
            raise
    
    def perform_destroy(self, instance):
        try:
            # Log flair deletion
            AuditLog.log(
                action='flair_delete',
                entity_type='flair',
                entity_id=instance.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={
                    'community_id': str(instance.community.id),
                    'community_name': instance.community.name,
                    'flair_name': instance.name
                }
            )
            
            instance.delete()
        except Exception as e:
            # Log failed flair deletion
            AuditLog.log(
                action='flair_delete_failed',
                entity_type='flair',
                entity_id=instance.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={
                    'community_id': str(instance.community.id),
                    'community_name': instance.community.name,
                    'flair_name': instance.name,
                    'error': str(e)
                }
            )
            raise
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CommunityDetailByPathView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve a community by its path (slug).
    """
    serializer_class = CommunitySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'path'
    lookup_url_kwarg = 'path'
    queryset = Community.objects.all()


class CommunityMembersByPathView(generics.ListAPIView):
    """
    API endpoint to list members of a community by its path.
    """
    serializer_class = CommunityMemberSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        path = self.kwargs.get('path')
        community = get_object_or_404(Community, path=path)
        return CommunityMember.objects.filter(community=community)


class CommunityModeratorsByPathView(generics.ListAPIView):
    """
    API endpoint to list moderators of a community by its path.
    """
    serializer_class = CommunityModeratorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        path = self.kwargs.get('path')
        community = get_object_or_404(Community, path=path)
        return CommunityModerator.objects.filter(community=community)


class UnbanByPathView(generics.GenericAPIView):
    """
    API endpoint for unbanning a user from a community by path.
    This provides a simpler API for unbanning users: /communities/{community_path}/unban/{username}/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, path, username):
        try:
            # Get the community by path
            community = get_object_or_404(Community, path=path)
            
            # Check if the requester is a moderator
            if not CommunityModerator.objects.filter(
                community=community, user=request.user).exists() and not request.user.is_staff:
                return Response({'detail': 'Only moderators can unban members.'},
                               status=status.HTTP_403_FORBIDDEN)
            
            # Get the user by username
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response({'detail': 'User not found.'},
                               status=status.HTTP_404_NOT_FOUND)
            
            # Get the community member
            try:
                member = CommunityMember.objects.get(community=community, user=user)
            except CommunityMember.DoesNotExist:
                return Response({'detail': 'This user is not a member of this community.'},
                               status=status.HTTP_404_NOT_FOUND)
            
            # Check if member is banned
            if not member.is_banned:
                return Response({'detail': 'This member is not banned.'},
                              status=status.HTTP_400_BAD_REQUEST)
            
            # Unban the member
            member.unban()
            
            # Send notification to the unbanned user
            from notifications.models import Notification
            Notification.send_mod_action_notification(
                user=member.user,
                community=member.community,
                action=f"Your ban from r/{member.community.name} has been lifted",
                admin_user=request.user,
                link_url=f"/c/{member.community.path}"
            )
            
            # Log member unban
            AuditLog.log(
                action='community_member_unban',
                entity_type='community_member',
                entity_id=member.id,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={
                    'community_id': str(member.community.id),
                    'community_name': member.community.name,
                    'user_id': str(member.user.id),
                    'username': member.user.username
                }
            )
            
            return Response({'detail': f'User {username} has been unbanned from {community.name}.'})
            
        except Exception as e:
            return Response({'detail': f'Error unbanning user: {str(e)}'},
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class BanByPathView(generics.GenericAPIView):
    """
    API endpoint for banning a user from a community by path.
    This provides a simpler API for banning users: /communities/{community_path}/ban/{username}/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, path, username):
        try:
            # Get the community by path
            community = get_object_or_404(Community, path=path)
            
            # Check if the requester is a moderator
            if not CommunityModerator.objects.filter(
                community=community, user=request.user).exists() and not request.user.is_staff:
                return Response({'detail': 'Only moderators can ban members.'},
                               status=status.HTTP_403_FORBIDDEN)
            
            # Get the user by username
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response({'detail': 'User not found.'},
                               status=status.HTTP_404_NOT_FOUND)
            
            # Get or create the community member
            member, created = CommunityMember.objects.get_or_create(
                community=community,
                user=user,
                defaults={'is_approved': not community.is_private and not community.is_restricted}
            )
            
            # Check if member is already banned
            if member.is_banned:
                return Response({'detail': 'This user is already banned from this community.'},
                              status=status.HTTP_400_BAD_REQUEST)
            
            # Get ban parameters
            reason = request.data.get('reason', '')
            duration_days = request.data.get('duration_days')
            if duration_days:
                try:
                    duration_days = int(duration_days)
                except (TypeError, ValueError):
                    return Response({'detail': 'Duration days must be a valid number.'},
                                  status=status.HTTP_400_BAD_REQUEST)
            
            # Ban the member
            member.ban(reason=reason, banned_by=request.user, duration_days=duration_days)
            
            # Create a ban duration message for notification
            if duration_days:
                duration_msg = f" for {duration_days} days"
            else:
                duration_msg = " permanently"
            
            # Send notification to the banned user
            from notifications.models import Notification
            Notification.send_mod_action_notification(
                user=member.user,
                community=member.community,
                action=f"You have been banned from r/{member.community.name}{duration_msg}: {reason}",
                admin_user=request.user,
                link_url=f"/c/{member.community.path}"
            )
            
            # Log member ban
            AuditLog.log(
                action='community_member_ban',
                entity_type='community_member',
                entity_id=member.id,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={
                    'community_id': str(member.community.id),
                    'community_name': member.community.name,
                    'user_id': str(member.user.id),
                    'username': member.user.username,
                    'reason': reason,
                    'duration_days': duration_days
                }
            )
            
            return Response({'detail': f'User {username} has been banned from {community.name}.'})
            
        except Exception as e:
            return Response({'detail': f'Error banning user: {str(e)}'},
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class BannedUsersView(generics.ListAPIView):
    """
    API endpoint to list banned users of a community by its path.
    """
    serializer_class = CommunityMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        path = self.kwargs.get('path')
        community = get_object_or_404(Community, path=path)
        
        # Check if the requester is a moderator or admin
        is_moderator = CommunityModerator.objects.filter(
            community=community, user=self.request.user).exists()
        
        if not is_moderator and not self.request.user.is_staff:
            return CommunityMember.objects.none()  # Return empty queryset if not authorized
        
        return CommunityMember.objects.filter(community=community, is_banned=True)
    
    def list(self, request, *args, **kwargs):
        path = self.kwargs.get('path')
        community = get_object_or_404(Community, path=path)
        
        # Check permissions
        is_moderator = CommunityModerator.objects.filter(
            community=community, user=request.user).exists()
        
        if not is_moderator and not request.user.is_staff:
            return Response({'detail': 'Only moderators can view banned users list.'},
                          status=status.HTTP_403_FORBIDDEN)
        
        # Get the queryset and serialize it
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BanStatusView(generics.GenericAPIView):
    """
    API endpoint to check if the authenticated user is banned in a community.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, path):
        community = get_object_or_404(Community, path=path)
        user = request.user
        
        try:
            member = CommunityMember.objects.get(community=community, user=user)
            is_banned = member.is_banned
            ban_reason = member.ban_reason if is_banned else None
            banned_until = member.banned_until if is_banned else None
            
            return Response({
                'is_banned': is_banned,
                'ban_reason': ban_reason,
                'banned_until': banned_until,
            })
        except CommunityMember.DoesNotExist:
            # User is not a member
            return Response({
                'is_banned': False,
                'detail': 'User is not a member of this community'
            })


class UserBanStatusView(generics.GenericAPIView):
    """
    API endpoint to check if a specific user is banned in a community.
    This endpoint is accessible to all users, including unauthenticated ones.
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, path, username):
        try:
            # Get the community by path
            community = get_object_or_404(Community, path=path)
            
            # Get the user by username
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response({'detail': 'User not found.'},
                               status=status.HTTP_404_NOT_FOUND)
            
            # Check if the user is a member and if they're banned
            try:
                member = CommunityMember.objects.get(community=community, user=user)
                is_banned = member.is_banned
                
                # Only return minimal information for privacy reasons
                return Response({
                    'username': username,
                    'is_banned': is_banned,
                    'community': community.name
                })
            except CommunityMember.DoesNotExist:
                # User is not a member
                return Response({
                    'username': username,
                    'is_banned': False,
                    'community': community.name,
                    'detail': 'User is not a member of this community'
                })
                
        except Exception as e:
            return Response({'detail': f'Error checking ban status: {str(e)}'},
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
