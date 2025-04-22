from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class BackblazeB2Storage(S3Boto3Storage):
    """
    Custom storage backend for Backblaze B2.
    
    This class extends S3Boto3Storage to work with Backblaze B2's S3-compatible API.
    """
    access_key = settings.B2_ACCESS_KEY
    secret_key = settings.B2_SECRET_KEY
    bucket_name = settings.B2_BUCKET_NAME
    region_name = settings.B2_REGION
    custom_domain = None
    
    # Backblaze B2 specific settings
    endpoint_url = f'https://s3.{settings.B2_REGION}.backblazeb2.com'
    file_overwrite = False
    object_parameters = settings.AWS_S3_OBJECT_PARAMETERS
    querystring_auth = settings.AWS_QUERYSTRING_AUTH
    default_acl = settings.AWS_DEFAULT_ACL

    def __init__(self, *args, **kwargs):
        # Backblaze B2 uses a different endpoint than AWS S3
        kwargs.setdefault('endpoint_url', self.endpoint_url)
        super().__init__(*args, **kwargs) 