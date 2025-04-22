from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from storage import post_image_storage, community_image_storage, profile_image_storage
from utils.media_validators import validate_image, generate_safe_filename
from security.models import AuditLog
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class ImageUploadView(APIView):
    """
    API view for handling image uploads to Backblaze B2.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Upload an image to Backblaze B2 storage",
        operation_summary="Upload image",
        manual_parameters=[
            openapi.Parameter(
                name='image',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description='Image file to upload'
            ),
            openapi.Parameter(
                name='type',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description='Image type (post, community, or profile)',
                enum=['post', 'community', 'profile'],
                default='post'
            ),
        ],
        responses={
            201: openapi.Response(
                description='Image uploaded successfully',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'url': openapi.Schema(type=openapi.TYPE_STRING, description='URL to the uploaded image'),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Indicates success')
                    }
                )
            ),
            400: openapi.Response(
                description='Bad request',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Indicates failure')
                    }
                )
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        if 'image' not in request.FILES:
            return Response(
                {"error": "No image file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        image_file = request.FILES['image']
        image_type = request.data.get('type', 'post')  # Default to post images
        
        try:
            # Validate image
            validate_image(image_file)
            
            # Generate safe filename
            safe_filename = generate_safe_filename(image_file.name)
            
            # Choose appropriate storage based on image type
            if image_type == 'post':
                storage = post_image_storage
                upload_path = f"posts/{safe_filename}"
            elif image_type == 'community':
                storage = community_image_storage
                upload_path = f"communities/{safe_filename}"
            elif image_type == 'profile':
                storage = profile_image_storage
                upload_path = f"profiles/{safe_filename}"
            else:
                return Response(
                    {"error": "Invalid image type. Must be 'post', 'community', or 'profile'."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Upload file to Backblaze B2
            file_path = storage.save(upload_path, image_file)
            
            # Get the URL
            file_url = storage.url(file_path)
            
            # Log image upload
            AuditLog.log(
                action='image_upload',
                entity_type=f'{image_type}_image',
                entity_id=None,  # We don't have an ID yet as the image isn't linked to an entity
                user=request.user,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={
                    'image_type': image_type,
                    'file_size': image_file.size,
                    'original_filename': image_file.name,
                    'stored_path': file_path
                }
            )
            
            return Response({
                'url': file_url,
                'success': True
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': str(e),
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
