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