# Reddit Clone

A modern Reddit clone built with Django REST Framework and Bunny.net media storage.

## Features

- User authentication with JWT
- Community creation and management
- Post creation with rich text and media
- Commenting system with nested replies
- Voting mechanism
- Media uploads to Bunny.net Storage
- Real-time notifications using WebSockets
- Search functionality
- Moderation tools
- Message system

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL
- Redis (for WebSockets and caching)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/reddit-clone.git
   cd reddit-clone
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following variables:
   ```
   DEBUG=True
   SECRET_KEY=your-secret-key
   ALLOWED_HOSTS=localhost,127.0.0.1
   DATABASE_URL=postgres://user:password@localhost:5432/redditclone
   REDIS_URL=redis://localhost:6379/0
   
   # Bunny.net Storage configuration
   USE_BUNNY_STORAGE=True
   BUNNY_STORAGE_API_KEY=your-api-key
   BUNNY_STORAGE_ZONE=your-storage-zone
   BUNNY_STORAGE_REGION=de  # Your preferred region (de, ny, sg, syd)
   # Optional: Custom domain if configured in Bunny.net
   BUNNY_STORAGE_URL=https://your-custom-domain.b-cdn.net/
   
   # Legacy Backblaze B2 configuration (not used if USE_BUNNY_STORAGE is True)
   USE_BACKBLAZE=False
   B2_ACCESS_KEY=your-access-key
   B2_SECRET_KEY=your-secret-key
   B2_BUCKET_NAME=your-bucket-name
   B2_REGION=eu-central-003
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

## API Documentation

The API is fully documented using Swagger/OpenAPI. Access the documentation at:

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`

These interactive documentation pages allow you to:
- Browse all available endpoints
- See request/response formats
- Test API calls directly from the browser
- Find models and schemas
- Understand authentication requirements

## Media Storage

The application uses Bunny.net Storage for storing media files. The storage system is configured to handle:

- Post images
- Community images
- User profile images

### Bunny.net Storage Setup

To use Bunny.net for media storage:

1. Create a Bunny.net account at https://bunny.net/
2. Create a Storage Zone in your desired region
3. Get your Storage API Key and Zone name
4. Update your `.env` file with the Bunny.net credentials
5. Set `USE_BUNNY_STORAGE=True` in your `.env` file

### Upload Endpoint

Media files can be uploaded using the `/api/v1/uploads/images/` endpoint:

```
POST /api/v1/uploads/images/
Content-Type: multipart/form-data
Authorization: JWT your-token

Parameters:
- image: The image file (required)
- type: Image type - "post", "community", or "profile" (optional, default: "post")

Response:
{
  "url": "https://your-storage-zone.b-cdn.net/path/to/image.jpg",
  "success": true
}
```

## Votes API

The voting system allows users to upvote or downvote posts and comments.

### Vote on a Post

```
POST /api/v1/votes/posts/{post_id}/vote/
Content-Type: application/json
Authorization: JWT your-token

Body:
{
  "content_type": "post",
  "content_id": 1121, // Replace with the actual post ID
  "vote_type": 1     // 1 for upvote, -1 for downvote
}
```

### Vote on a Comment

```
POST /api/v1/votes/comments/{comment_id}/vote/
Content-Type: application/json
Authorization: JWT your-token

Body:
{
  "content_type": "comment",
  "content_id": 1121, // Replace with the actual comment ID
  "vote_type": 1     // 1 for upvote, -1 for downvote
}
```

## Project Structure

- `/reddit_clone/` - Main project folder
  - `/reddit_clone/` - Project settings
  - `/users/` - User management
  - `/communities/` - Community management
  - `/posts/` - Post creation and management
  - `/comments/` - Comment system
  - `/uploads/` - Media upload handling
  - `/votes/` - Voting system
  - `/messaging/` - Private messaging
  - `/notifications/` - User notifications
  - `/moderation/` - Moderation tools
  - `/security/` - Security utilities
  - `/search/` - Search functionality
  - `/core/` - Core utilities

## Development

### Backend Development

- The project follows Django REST Framework conventions
- Models are in `models.py` files
- API views are in `views.py` files
- URL configurations are in `urls.py` files
- Serializers are in `serializers.py` files

### Frontend Development

For frontend development, you can use the Swagger documentation to understand available endpoints. The API follows these conventions:

- Authentication uses JWT tokens (`Authorization: JWT your-token`)
- API endpoints follow RESTful conventions
- Nested resources are represented in the URL structure
- Pagination is provided for list endpoints
- Filtering is available via query parameters

## WebSockets

Real-time features are implemented using Django Channels. WebSocket connections are available at:

- `/ws/posts/` - For post updates
- `/ws/notifications/` - For user notifications

## Security

The application implements multiple security measures:

- JWT authentication with refresh tokens
- CSRF protection
- XSS prevention
- Rate limiting
- Input validation
- CORS configuration

## Deployment

The application is designed to be deployed to a production environment with:

- Gunicorn as the WSGI server
- Daphne as the ASGI server (for WebSockets)
- PostgreSQL for the database
- Redis for caching and Channels
- Bunny.net for media storage

## License

This project is licensed under the MIT License - see the LICENSE file for details.
