import os
from django.conf import settings
from django.core.files.storage import Storage
from storages.backends.s3boto3 import S3Boto3Storage

class BackblazeB2Storage(S3Boto3Storage):
    """
    Storage backend for Backblaze B2.
    Uses the boto3 S3 client but configured for Backblaze B2.
    """
    access_key = os.environ.get('B2_ACCESS_KEY')
    secret_key = os.environ.get('B2_SECRET_KEY')
    bucket_name = os.environ.get('B2_BUCKET_NAME')
    endpoint_url = f"https://s3.{os.environ.get('B2_REGION', 'us-west-004')}.backblazeb2.com"
    region_name = os.environ.get('B2_REGION', 'us-west-004')
    custom_domain = os.environ.get('B2_CUSTOM_DOMAIN')
    file_overwrite = False
    default_acl = 'public-read'
    object_parameters = {'CacheControl': 'max-age=86400'}
    
    def get_available_name(self, name, max_length=None):
        """
        Returns a filename that's free on the target storage system.
        Adds a UUID to ensure uniqueness.
        """
        import uuid
        
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        
        # Add UUID to filename to ensure uniqueness
        uuid_str = str(uuid.uuid4())
        name = os.path.join(dir_name, f"{file_root}_{uuid_str}{file_ext}")
        
        return super().get_available_name(name, max_length)

# Create instances for different media types
post_image_storage = BackblazeB2Storage(location='post-images')
community_image_storage = BackblazeB2Storage(location='community-images')
profile_image_storage = BackblazeB2Storage(location='profile-images') 