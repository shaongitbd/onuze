# SecureThread - Uploads API Endpoints

This document describes the available API endpoints for uploading media files in the SecureThread application.

## Core Upload Endpoints

### Media Upload Endpoint

- `POST /uploads/media/` - Upload an image or video file
  - Requires authentication
  - Form data parameters:
    - `file` - The image or video file to upload
    - `type` - Media context type [post|community|profile] (default: post)
  - Response:
    - `url` - URL to the uploaded media
    - `success` - Boolean indicating success
    - `media_type` - Detected media type (image or video)

## Features

### File Type Support
The upload API supports:
- Images (jpg, jpeg, png, gif, webp)
- Videos (mp4, webm, mov)

### Validation
Uploaded files are validated for:
- File type (must be an allowed image or video format)
- File size (maximum size limits for images and videos)
- Content safety (potential future enhancement)

### Storage
- Files are stored on Bunny.net's storage service
- Files are organized by context type:
  - `posts/` - Media for post content
  - `communities/` - Media for community banners and icons
  - `profiles/` - Media for user profile pictures

### Security Features
- Filenames are sanitized to prevent path traversal attacks
- File content types are validated
- Authentication required to prevent unauthorized uploads
- Logging of all media uploads for audit purposes

### Integration
The upload API is used by:
- Post creation/editing to attach media
- Community profile updates for banner and icon images
- User profile updates for profile pictures 