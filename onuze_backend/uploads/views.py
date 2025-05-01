from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
import logging
from storage import post_image_storage, community_image_storage, profile_image_storage
from utils.media_validators import validate_image, validate_video, generate_safe_filename, ValidationError
from security.models import AuditLog
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

logger = logging.getLogger('django')

class MediaUploadView(APIView):
    """
    API view for handling image and video uploads to Bunny.net Storage.
    Accepts 'file' parameter instead of 'image'.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Upload an image or video file to Bunny.net storage",
        operation_summary="Upload Media (Image/Video)",
        manual_parameters=[
            openapi.Parameter(
                name='file', # Changed from 'image'
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description='Image or video file to upload'
            ),
            openapi.Parameter(
                name='type',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description='Media context type (post, community, or profile)',
                enum=['post', 'community', 'profile'],
                default='post'
            ),
        ],
        responses={
            201: openapi.Response(
                description='Media uploaded successfully',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'url': openapi.Schema(type=openapi.TYPE_STRING, description='URL to the uploaded media'),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Indicates success'),
                        'media_type': openapi.Schema(type=openapi.TYPE_STRING, description='Detected media type (image or video)')
                    }
                )
            ),
            400: openapi.Response(
                description='Bad request (e.g., invalid file type, size exceeded)',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Indicates failure')
                    }
                )
            ),
            500: openapi.Response(
                description='Server error during upload process',
                 schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Indicates failure')
                    }
                )
            )
        }
    )
    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return Response(
                {"error": "No file provided. Use the 'file' parameter.", "success": False},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        uploaded_file = request.FILES['file']
        context_type = request.data.get('type', 'post')  # post, community, profile
        detected_media_type = None
        
        try:
            # Determine media type and validate
            content_type = getattr(uploaded_file, 'content_type', '')
            if content_type.startswith('image/'):
                detected_media_type = 'image'
                validate_image(uploaded_file)
            elif content_type.startswith('video/'):
                detected_media_type = 'video'
                validate_video(uploaded_file)
            else:
                raise ValidationError(f"Unsupported file type: {content_type}. Please upload an image or video.")
            
            # Generate safe filename
            safe_filename = generate_safe_filename(uploaded_file.name)
            
            # Choose appropriate storage based on context type
            if context_type == 'post':
                storage = post_image_storage # Using combined storage for now
                upload_path = f"posts/{safe_filename}"
            elif context_type == 'community':
                storage = community_image_storage
                upload_path = f"communities/{safe_filename}"
            elif context_type == 'profile':
                storage = profile_image_storage
                upload_path = f"profiles/{safe_filename}"
            else:
                return Response(
                    {"error": "Invalid context type. Must be 'post', 'community', or 'profile'.", "success": False},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Upload file to Bunny.net Storage
            try:
                file_path = storage.save(upload_path, uploaded_file)
                file_url = storage.url(file_path)
                
                # Log media upload
                AuditLog.log(
                    action=f'{detected_media_type}_upload',
                    entity_type=f'{context_type}_{detected_media_type}',
                    user=request.user,
                    ip_address=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details={
                        'context_type': context_type,
                        'detected_media_type': detected_media_type,
                        'file_size': uploaded_file.size,
                        'original_filename': uploaded_file.name,
                        'stored_path': file_path,
                        'storage_provider': 'bunny.net'
                    }
                )
                
                return Response({
                    'url': file_url,
                    'success': True,
                    'media_type': detected_media_type
                }, status=status.HTTP_201_CREATED)
                
            except IOError as e:
                logger.error(f"Bunny.net upload failed: {str(e)}", exc_info=True)
                return Response({
                    'error': f"Storage upload error: {str(e)}",
                    'success': False
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except ValidationError as e:
            # Handle validation errors (wrong type, size, etc.)
            return Response({
                'error': str(e),
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Catch-all for other unexpected errors
            logger.error(f"Unexpected error in media upload: {str(e)}", exc_info=True)
            return Response({
                'error': "An unexpected server error occurred.",
                'success': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
