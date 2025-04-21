from django.shortcuts import render
from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Report, BanAppeal
from .serializers import ReportSerializer, BanAppealSerializer
from communities.models import Community, CommunityModerator
from security.models import AuditLog
from django.db.models import Q


class ReportViewSet(viewsets.ModelViewSet):
    """
    API endpoint for handling reports.
    Users can create reports.
    Moderators/Admins can view, resolve, or reject reports.
    """
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admins see all reports
        if user.is_staff:
            return Report.objects.all()
        
        # Moderators see reports for their communities
        moderated_communities = CommunityModerator.objects.filter(user=user).values_list('community_id', flat=True)
        if moderated_communities:
            return Report.objects.filter(community_id__in=moderated_communities)
        
        # Regular users can only see reports they made
        return Report.objects.filter(reporter=user)
    
    def perform_create(self, serializer):
        try:
            report = serializer.save()
            # Log report creation
            AuditLog.log(
                action='report_create',
                entity_type='report',
                entity_id=report.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={
                    'content_type': report.content_type,
                    'content_id': str(report.content_id),
                    'reason': report.reason
                }
            )
        except Exception as e:
            AuditLog.log(
                action='report_create_failed',
                entity_type='report',
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={
                    'content_type': serializer.validated_data.get('content_type'),
                    'content_id': str(serializer.validated_data.get('content_id')),
                    'reason': serializer.validated_data.get('reason'),
                    'error': str(e)
                }
            )
            raise
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def resolve(self, request, pk=None):
        report = self.get_object()
        user = request.user
        
        # Check permissions (Moderator of community or Admin)
        is_moderator = CommunityModerator.objects.filter(user=user, community=report.community).exists()
        if not user.is_staff and not is_moderator:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
            
        notes = request.data.get('notes', '')
        report.resolve(resolved_by=user, notes=notes)
        
        # Log report resolution
        AuditLog.log(
            action='report_resolve',
            entity_type='report',
            entity_id=report.id,
            user=user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            status='success',
            details={'notes': notes}
        )
        
        return Response(self.get_serializer(report).data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        report = self.get_object()
        user = request.user
        
        # Check permissions (Moderator of community or Admin)
        is_moderator = CommunityModerator.objects.filter(user=user, community=report.community).exists()
        if not user.is_staff and not is_moderator:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
            
        notes = request.data.get('notes', '')
        report.reject(resolved_by=user, notes=notes)
        
        # Log report rejection
        AuditLog.log(
            action='report_reject',
            entity_type='report',
            entity_id=report.id,
            user=user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            status='success',
            details={'notes': notes}
        )
        
        return Response(self.get_serializer(report).data)
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CommunityReportListView(generics.ListAPIView):
    """
    API endpoint for listing reports specific to a community.
    Requires moderator or admin permissions.
    """
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        community_id = self.kwargs.get('community_id')
        community = get_object_or_404(Community, id=community_id)
        
        # Check permissions (Moderator of community or Admin)
        is_moderator = CommunityModerator.objects.filter(user=user, community=community).exists()
        if not user.is_staff and not is_moderator:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to view reports for this community.")
            
        # Filter by status
        status_filter = self.request.query_params.get('status', Report.PENDING)
        return Report.objects.filter(community=community, status=status_filter).order_by('-created_at')


class BanAppealViewSet(viewsets.ModelViewSet):
    """
    API endpoint for handling ban appeals.
    Users can create appeals for their bans.
    Moderators/Admins can view and manage appeals.
    """
    serializer_class = BanAppealSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admins see all site ban appeals and appeals for communities they moderate
        if user.is_staff:
            moderated_communities = CommunityModerator.objects.filter(user=user).values_list('community_id', flat=True)
            return BanAppeal.objects.filter(
                Q(appeal_type=BanAppeal.SITE_BAN) | Q(community_id__in=moderated_communities)
            ).order_by('-created_at')
        
        # Moderators see appeals for their communities
        moderated_communities = CommunityModerator.objects.filter(user=user).values_list('community_id', flat=True)
        if moderated_communities:
            return BanAppeal.objects.filter(community_id__in=moderated_communities).order_by('-created_at')
        
        # Regular users can only see their own appeals
        return BanAppeal.objects.filter(user=user).order_by('-created_at')
    
    def perform_create(self, serializer):
        try:
            appeal = serializer.save()
            # Log appeal creation
            AuditLog.log(
                action='ban_appeal_create',
                entity_type='ban_appeal',
                entity_id=appeal.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={
                    'appeal_type': appeal.appeal_type,
                    'community_id': str(appeal.community.id) if appeal.community else None
                }
            )
        except Exception as e:
            AuditLog.log(
                action='ban_appeal_create_failed',
                entity_type='ban_appeal',
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={
                    'appeal_type': serializer.validated_data.get('appeal_type'),
                    'error': str(e)
                }
            )
            raise
            
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def approve(self, request, pk=None):
        appeal = self.get_object()
        user = request.user
        
        # Check permissions
        if not self.can_review_appeal(user, appeal):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
            
        notes = request.data.get('notes', '')
        response_to_user = request.data.get('response', '')
        appeal.approve(reviewed_by=user, notes=notes, response=response_to_user)
        
        # Log appeal approval
        AuditLog.log(
            action='ban_appeal_approve',
            entity_type='ban_appeal',
            entity_id=appeal.id,
            user=user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            status='success',
            details={'notes': notes, 'response': response_to_user}
        )
        
        return Response(self.get_serializer(appeal).data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        appeal = self.get_object()
        user = request.user
        
        # Check permissions
        if not self.can_review_appeal(user, appeal):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
            
        notes = request.data.get('notes', '')
        response_to_user = request.data.get('response', '')
        appeal.reject(reviewed_by=user, notes=notes, response=response_to_user)
        
        # Log appeal rejection
        AuditLog.log(
            action='ban_appeal_reject',
            entity_type='ban_appeal',
            entity_id=appeal.id,
            user=user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            status='success',
            details={'notes': notes, 'response': response_to_user}
        )
        
        return Response(self.get_serializer(appeal).data)

    def can_review_appeal(self, user, appeal):
        """Check if a user has permission to review a specific appeal."""
        if user.is_staff:
            return True
        if appeal.appeal_type == BanAppeal.COMMUNITY_BAN and appeal.community:
            return CommunityModerator.objects.filter(user=user, community=appeal.community).exists()
        return False
        
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
