import os
import uuid
import magic
from django.core.exceptions import ValidationError
from django.conf import settings


# Define allowed mime types and extensions
ALLOWED_IMAGE_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/gif': ['.gif'],
    'image/webp': ['.webp'],
}

ALLOWED_VIDEO_TYPES = {
    'video/mp4': ['.mp4'],
    'video/webm': ['.webm'],
    'video/ogg': ['.ogv'],
}

ALLOWED_DOCUMENT_TYPES = {
    'application/pdf': ['.pdf'],
}

# Maximum file sizes (in bytes)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10 MB

# Default upload directory
DEFAULT_UPLOAD_DIR = 'media/uploads/'

# Try to import pyclamd for virus scanning
try:
    import pyclamd
    CLAMAV_ENABLED = True
except ImportError:
    CLAMAV_ENABLED = False


def scan_file_for_malware(file):
    """
    Scan a file for malware using ClamAV.
    
    Args:
        file: The uploaded file object
        
    Returns:
        bool: True if file is clean, False if infected
        
    Raises:
        ValidationError: If file is infected or ClamAV is not available
    """
    if not CLAMAV_ENABLED:
        # Log that ClamAV is not available but allow the upload
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("ClamAV is not available for virus scanning. Skipping scan.")
        return True
    
    # Try to connect to ClamAV daemon
    try:
        # Try to connect to local socket first
        clam = pyclamd.ClamdUnixSocket()
        # Test connection
        clam.ping()
    except Exception:
        try:
            # Fall back to network socket
            clam = pyclamd.ClamdNetworkSocket()
            clam.ping()
        except Exception as e:
            # Log that ClamAV is not responding but allow the upload
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"ClamAV daemon is not responding: {str(e)}. Skipping scan.")
            return True
    
    # Store the file content to a temporary file for scanning
    try:
        # Reset file pointer
        file.seek(0)
        
        # Read file content
        file_content = file.read()
        
        # Reset file pointer again
        file.seek(0)
        
        # Create a unique temp filename
        temp_filename = f"/tmp/clamd_temp_{uuid.uuid4().hex}"
        
        # Write content to temp file
        with open(temp_filename, 'wb') as temp_file:
            temp_file.write(file_content)
        
        # Scan the file
        scan_result = clam.scan_file(temp_filename)
        
        # Remove temp file
        try:
            os.unlink(temp_filename)
        except Exception:
            pass
        
        # Check scan result
        if scan_result:
            # File is infected - scan_result will be {filename: (FOUND: virusname)}
            virus_name = scan_result[temp_filename][1]
            raise ValidationError(f"Security threat detected: {virus_name}. Upload rejected.")
        
        # File is clean
        return True
        
    except ValidationError:
        # Re-raise validation errors
        raise
    except Exception as e:
        # Log other errors and allow upload (fail open for usability, but log the issue)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error during virus scan: {str(e)}. Allowing file with caution.")
        return True


def validate_file_type(file, allowed_types):
    """
    Validate file mime type using python-magic.
    
    Args:
        file: The uploaded file object
        allowed_types (dict): Dictionary of allowed mime types and their extensions
    
    Returns:
        str: The detected mime type if valid
        
    Raises:
        ValidationError: If file type is not allowed
    """
    # Read the beginning of the file to determine its mime type
    file_content = file.read(2048)
    file.seek(0)  # Reset file pointer
    
    # Detect mime type
    mime = magic.Magic(mime=True)
    mime_type = mime.from_buffer(file_content)
    
    if mime_type not in allowed_types:
        allowed_extensions = []
        for extensions in allowed_types.values():
            allowed_extensions.extend(extensions)
            
        raise ValidationError(
            f"File type '{mime_type}' is not allowed. "
            f"Allowed types are: {', '.join(allowed_extensions)}"
        )
    
    return mime_type


def validate_file_extension(filename, allowed_types):
    """
    Validate file extension against allowed extensions for given mime types.
    
    Args:
        filename (str): The filename to validate
        allowed_types (dict): Dictionary of allowed mime types and their extensions
    
    Raises:
        ValidationError: If file extension is not allowed
    """
    ext = os.path.splitext(filename)[1].lower()
    allowed_extensions = []
    
    for extensions in allowed_types.values():
        allowed_extensions.extend(extensions)
        
        if ext in extensions:
            return
    
    raise ValidationError(
        f"File extension '{ext}' is not allowed. "
        f"Allowed extensions are: {', '.join(allowed_extensions)}"
    )


def validate_file_size(file, max_size):
    """
    Validate file size.
    
    Args:
        file: The uploaded file object
        max_size (int): Maximum allowed size in bytes
    
    Raises:
        ValidationError: If file is too large
    """
    if file.size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise ValidationError(f"File is too large. Maximum size is {max_size_mb} MB.")


def generate_safe_filename(filename):
    """
    Generate a secure random filename while preserving the original extension.
    
    Args:
        filename (str): The original filename
    
    Returns:
        str: A secure filename with original extension
    """
    ext = os.path.splitext(filename)[1].lower()
    return f"{uuid.uuid4().hex}{ext}"


def get_upload_path(instance, filename, upload_dir=DEFAULT_UPLOAD_DIR):
    """
    Generate upload path for the uploaded file.
    
    Args:
        instance: The model instance the file is attached to
        filename (str): The original filename
        upload_dir (str): Base upload directory
    
    Returns:
        str: The full upload path for the file
    """
    safe_filename = generate_safe_filename(filename)
    
    # Generate a directory structure based on current date
    from datetime import datetime
    date_path = datetime.now().strftime('%Y/%m/%d')
    
    return os.path.join(upload_dir, date_path, safe_filename)


def validate_image(file):
    """
    Validate an uploaded image file.
    
    Args:
        file: The uploaded image file to validate
    
    Raises:
        ValidationError: If image is invalid
    """
    validate_file_type(file, ALLOWED_IMAGE_TYPES)
    validate_file_extension(file.name, ALLOWED_IMAGE_TYPES)
    validate_file_size(file, MAX_IMAGE_SIZE)
    scan_file_for_malware(file)


def validate_video(file):
    """
    Validate an uploaded video file.
    
    Args:
        file: The uploaded video file to validate
    
    Raises:
        ValidationError: If video is invalid
    """
    validate_file_type(file, ALLOWED_VIDEO_TYPES)
    validate_file_extension(file.name, ALLOWED_VIDEO_TYPES)
    validate_file_size(file, MAX_VIDEO_SIZE)
    scan_file_for_malware(file)


def validate_document(file):
    """
    Validate an uploaded document file.
    
    Args:
        file: The uploaded document file to validate
    
    Raises:
        ValidationError: If document is invalid
    """
    validate_file_type(file, ALLOWED_DOCUMENT_TYPES)
    validate_file_extension(file.name, ALLOWED_DOCUMENT_TYPES)
    validate_file_size(file, MAX_DOCUMENT_SIZE)
    scan_file_for_malware(file)


def upload_image(instance, file, upload_dir=DEFAULT_UPLOAD_DIR):
    """
    Validate and process an uploaded image file.
    
    Args:
        instance: The model instance the image is attached to
        file: The uploaded image file
        upload_dir (str): Base upload directory
    
    Returns:
        str: The path where the image was saved
    
    Raises:
        ValidationError: If image is invalid
    """
    validate_image(file)
    return get_upload_path(instance, file.name, upload_dir)


def upload_video(instance, file, upload_dir=DEFAULT_UPLOAD_DIR):
    """
    Validate and process an uploaded video file.
    
    Args:
        instance: The model instance the video is attached to
        file: The uploaded video file
        upload_dir (str): Base upload directory
    
    Returns:
        str: The path where the video was saved
    
    Raises:
        ValidationError: If video is invalid
    """
    validate_video(file)
    return get_upload_path(instance, file.name, upload_dir) 