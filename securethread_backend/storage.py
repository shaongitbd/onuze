import os
import uuid
import requests
from urllib.parse import urljoin
from django.conf import settings
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
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


@deconstructible
class BunnyStorage(Storage):
    """
    Storage backend for Bunny.net Storage.
    Uses direct API requests to the Bunny.net Storage API.
    """
    def __init__(self, location=None):
        self.api_key = os.environ.get('BUNNY_STORAGE_API_KEY')
        self.storage_zone = os.environ.get('BUNNY_STORAGE_ZONE')
        self.region = os.environ.get('BUNNY_STORAGE_REGION', 'de')
        self.base_url = os.environ.get('BUNNY_STORAGE_URL', f'https://{self.storage_zone}.b-cdn.net/')
        self.api_url = f'https://storage.bunnycdn.com/{self.storage_zone}/'
        self.location = location

    def _get_full_path(self, name):
        """Get the full path including location folder if specified."""
        if self.location:
            # Always use forward slashes for Bunny.net
            path = f"{self.location}/{name}"
        else:
            path = name
            
        # Replace backslashes with forward slashes
        return path.replace('\\', '/')
        
    def _open(self, name, mode='rb'):
        """
        Retrieve the specified file from Bunny.net storage.
        """
        full_path = self._get_full_path(name)
        url = urljoin(self.api_url, full_path)
        
        headers = {
            'AccessKey': self.api_key
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Create a Django File object from the response content
            from django.core.files.base import ContentFile
            return ContentFile(response.content)
        except requests.exceptions.RequestException as e:
            raise IOError(f"Error retrieving file from Bunny.net: {str(e)}")
    
    def _save(self, name, content):
        """
        Save a new file to Bunny.net storage.
        """
        # --- TEMPORARY DEBUGGING --- 
        print(f"[DEBUG] BunnyStorage API Key being used: {self.api_key[:5]}...{self.api_key[-5:] if self.api_key else 'None'}")
        # --- END TEMPORARY DEBUGGING ---
        
        # Generate a unique filename
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        uuid_str = str(uuid.uuid4())
        # Always use forward slashes for directory paths
        dir_name = dir_name.replace('\\', '/')
        unique_name = f"{dir_name}/{file_root}_{uuid_str}{file_ext}" if dir_name else f"{file_root}_{uuid_str}{file_ext}"
        
        # Get the full path
        full_path = self._get_full_path(unique_name)
        url = urljoin(self.api_url, full_path)
        
        # Prepare headers
        headers = {
            'AccessKey': self.api_key,
            'Content-Type': 'application/octet-stream'
        }
        
        # Read file content
        content.seek(0)
        file_content = content.read()
        
        # Upload to Bunny.net with error handling
        try:
            response = requests.put(url, data=file_content, headers=headers)
            response.raise_for_status()
            return unique_name
        except requests.exceptions.RequestException as e:
            raise IOError(f"Failed to save file to Bunny.net: {str(e)}")
        
    def url(self, name):
        """
        Return the URL where the file can be accessed.
        """
        full_path = self._get_full_path(name)
        # Ensure we're using proper URL encoding and forward slashes
        encoded_path = '/'.join([part for part in full_path.split('/') if part])
        return urljoin(self.base_url, encoded_path)
    
    def delete(self, name):
        """
        Delete a file from Bunny.net storage.
        """
        full_path = self._get_full_path(name)
        url = urljoin(self.api_url, full_path)
        
        headers = {
            'AccessKey': self.api_key
        }
        
        try:
            response = requests.delete(url, headers=headers)
            
            if response.status_code != 204 and response.status_code != 404:
                raise IOError(f"Failed to delete file from Bunny.net: {response.content}")
        except requests.exceptions.RequestException as e:
            raise IOError(f"Error connecting to Bunny.net: {str(e)}")
    
    def exists(self, name):
        """
        Check if a file exists in Bunny.net storage.
        """
        full_path = self._get_full_path(name)
        url = urljoin(self.api_url, full_path)
        
        headers = {
            'AccessKey': self.api_key
        }
        
        try:
            response = requests.head(url, headers=headers)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def size(self, name):
        """
        Return the size of a file in bytes.
        """
        full_path = self._get_full_path(name)
        url = urljoin(self.api_url, full_path)
        
        headers = {
            'AccessKey': self.api_key
        }
        
        try:
            response = requests.head(url, headers=headers)
            if response.status_code != 200:
                raise ValueError("File doesn't exist")
            
            return int(response.headers.get('Content-Length', 0))
        except requests.exceptions.RequestException as e:
            raise IOError(f"Error checking file size on Bunny.net: {str(e)}")


# Use BunnyStorage for media files
post_image_storage = BunnyStorage(location='post-images')
community_image_storage = BunnyStorage(location='community-images')
profile_image_storage = BunnyStorage(location='profile-images') 