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


class CommunityViewSet(viewsets.ModelViewSet):
    print("YO")
    """
    API endpoint for communities.
    """
    queryset = Community.objects.all()
    print(queryset)
    serializer_class = CommunitySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsCommunityOwnerOrReadOnly]
    
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
    def join(self, request, pk=None):
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
            community.member_count = F('member_count') + 1
            community.save(update_fields=['member_count'])
            # Refresh from db to get the updated value
            community.refresh_from_db()
        
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
    def leave(self, request, pk=None):
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
                # Decrement member count
                community.member_count = F('member_count') - 1
                community.save(update_fields=['member_count'])
                # Refresh from db to get the updated value
                community.refresh_from_db()
            
            # Delete membership and any moderator status
            membership.delete()
            CommunityModerator.objects.filter(community=community, user=user).delete()
            
            return Response({'detail': 'Left community successfully.'})
            
        except CommunityMember.DoesNotExist:
            return Response({'detail': 'Not a member of this community.'},
                           status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        community = self.get_object()
        members = CommunityMember.objects.filter(community=community, is_approved=True)
        serializer = CommunityMemberSerializer(members, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def moderators(self, request, pk=None):
        community = self.get_object()
        moderators = CommunityModerator.objects.filter(community=community)
        serializer = CommunityModeratorSerializer(moderators, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def rules(self, request, pk=None):
        community = self.get_object()
        rules = CommunityRule.objects.filter(community=community)
        serializer = CommunityRuleSerializer(rules, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='settings', url_name='settings')
    def list_settings(self, request, pk=None):
        community = self.get_object()
        settings_qs = CommunitySetting.objects.filter(community=community)
        serializer = CommunitySettingSerializer(settings_qs, many=True)
        return Response(serializer.data)
    
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
    """
    serializer_class = CommunityMemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommunityModeratorOrReadOnly]
    
    def get_queryset(self):
        return CommunityMember.objects.all()
    
    def perform_create(self, serializer):
        member = serializer.save()
        
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
                'is_approved': member.is_approved
            }
        )
    
    def perform_update(self, serializer):
        member = serializer.save()
        
        # Log member update
        AuditLog.log(
            action='community_member_update',
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
                'is_approved': member.is_approved,
                'updated_fields': list(serializer.validated_data.keys())
            }
        )
    
    def perform_destroy(self, instance):
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
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        member = self.get_object()
        
        # Check if the requester is a moderator
        if not CommunityModerator.objects.filter(
            community=member.community, user=request.user).exists():
            return Response({'detail': 'Only moderators can approve members.'},
                           status=status.HTTP_403_FORBIDDEN)
        
        member.is_approved = True
        member.save()
        
        # Log member approval
        AuditLog.log(
            action='community_member_approve',
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
        
        return Response({'detail': 'Member approved successfully.'})
    
    @action(detail=True, methods=['post'])
    def ban(self, request, pk=None):
        member = self.get_object()
        
        # Check if the requester is a moderator
        if not CommunityModerator.objects.filter(
            community=member.community, user=request.user).exists() and not request.user.is_staff:
            return Response({'detail': 'Only moderators can ban members.'},
                           status=status.HTTP_403_FORBIDDEN)
        
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
        
        return Response({'detail': 'Member banned successfully.'})
    
    @action(detail=True, methods=['post'])
    def unban(self, request, pk=None):
        member = self.get_object()
        
        # Check if the requester is a moderator
        if not CommunityModerator.objects.filter(
            community=member.community, user=request.user).exists() and not request.user.is_staff:
            return Response({'detail': 'Only moderators can unban members.'},
                           status=status.HTTP_403_FORBIDDEN)
        
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
        
        return Response({'detail': 'Member unbanned successfully.'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        member = self.get_object()
        
        # Check if the requester is a moderator
        if not CommunityModerator.objects.filter(
            community=member.community, user=request.user).exists():
            return Response({'detail': 'Only moderators can reject members.'},
                           status=status.HTTP_403_FORBIDDEN)
        
        # Log member rejection before deletion
        AuditLog.log(
            action='community_member_reject',
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
        
        member.delete()
        return Response({'detail': 'Member rejected successfully.'})
    
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
    """
    serializer_class = CommunityModeratorSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommunityOwnerOrReadOnly]
    
    def get_queryset(self):
        return CommunityModerator.objects.all()
    
    def perform_create(self, serializer):
        moderator = serializer.save()
        
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
    
    def perform_update(self, serializer):
        moderator = serializer.save()
        
        # Log moderator update
        AuditLog.log(
            action='community_moderator_update',
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
                'is_owner': moderator.is_owner,
                'updated_fields': list(serializer.validated_data.keys())
            }
        )
    
    def perform_destroy(self, instance):
        # Prevent removal of the community owner
        if instance.is_owner:
            raise permissions.PermissionDenied("Cannot remove the community owner.")
        
        # Log moderator removal
        AuditLog.log(
            action='community_moderator_remove',
            entity_type='community_moderator',
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
    
    @action(detail=False, methods=['post'])
    def transfer_ownership(self, request):
        community_id = request.data.get('community')
        new_owner_id = request.data.get('new_owner')
        
        if not community_id or not new_owner_id:
            return Response({'detail': 'Community and new owner must be specified.'},
                           status=status.HTTP_400_BAD_REQUEST)
        
        community = get_object_or_404(Community, id=community_id)
        new_owner = get_object_or_404(CommunityModerator, community=community, user__id=new_owner_id)
        
        # Check if the requester is the current owner
        try:
            current_owner = CommunityModerator.objects.get(
                community=community, is_owner=True)
            
            if current_owner.user != request.user:
                return Response({'detail': 'Only the community owner can transfer ownership.'},
                               status=status.HTTP_403_FORBIDDEN)
            
            # Transfer ownership
            current_owner.is_owner = False
            current_owner.save()
            
            new_owner.is_owner = True
            new_owner.save()
            
            # Update the community owner
            community.created_by = new_owner.user
            community.save()
            
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
                    'new_owner_id': str(new_owner.user.id),
                    'new_owner_username': new_owner.user.username
                }
            )
            
            return Response({'detail': 'Ownership transferred successfully.'})
            
        except CommunityModerator.DoesNotExist:
            return Response({'detail': 'Community owner not found.'},
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
    """
    serializer_class = CommunityRuleSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommunityModeratorOrReadOnly]
    
    def get_queryset(self):
        return CommunityRule.objects.all()
    
    def perform_create(self, serializer):
        rule = serializer.save()
        
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
    
    def perform_update(self, serializer):
        rule = serializer.save()
        
        # Log rule update
        AuditLog.log(
            action='community_rule_update',
            entity_type='community_rule',
            entity_id=rule.id,
            user=self.request.user,
            ip_address=self.get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details={
                'community_id': str(rule.community.id),
                'community_name': rule.community.name,
                'rule_title': rule.title,
                'updated_fields': list(serializer.validated_data.keys())
            }
        )
    
    def perform_destroy(self, instance):
        # Log rule deletion
        AuditLog.log(
            action='community_rule_delete',
            entity_type='community_rule',
            entity_id=instance.id,
            user=self.request.user,
            ip_address=self.get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details={
                'community_id': str(instance.community.id),
                'community_name': instance.community.name,
                'rule_title': instance.title
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
    """
    serializer_class = FlairSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommunityModeratorOrReadOnly]
    
    def get_queryset(self):
        return Flair.objects.filter(community__id=self.kwargs.get('community_id', None))
    
    def perform_create(self, serializer):
        try:
            community_id = self.kwargs.get('community_id')
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
                    'community_id': self.kwargs.get('community_id'),
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
