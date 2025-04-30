# SecureThread

Welcome to the official SecureThread repository. This application is built by [shaongitbd](https://github.com/shaongitbd). For any problem feel free to mail me at shaongit@gmail.com

## License

**CC BY-NC 4.0 with additional attribution requirement**

You may use, modify, and share this project for **non-commercial purposes** only, provided that:

1. You give **clear attribution** to the original author.
2. If used on a **public-facing website**, a visible credit such as "Powered by SecureThread" with a link to the original repository must be shown on the website.

Commercial use, redistribution for profit, or use in paid services is **strictly prohibited** without a separate commercial license agreement.

## Technology Stack

### Frontend
Our frontend is built using Next.js. You can find the frontend content in the `frontend` folder.

### Backend
Our backend is developed using Django. It supports hundreds of endpoints with various filtering options and WebSocket capabilities. Note: We are not currently utilizing all the endpoints for our frontend; we will be adding those to our frontend gradually.

## API Documentation

### Community Endpoints

#### Collection Endpoints
- `GET /communities/` - List all communities
- `POST /communities/` - Create a new community
- `GET /communities/popular/` - Get the top 5 communities based on member count

#### Detail Endpoints
- `GET /communities/{path}/` - Get community details by path
- `PUT /communities/{path}/` - Update a community (owner only)
- `PATCH /communities/{path}/` - Partially update a community (owner only)
- `DELETE /communities/{path}/` - Delete a community (owner only)

[See all community endpoints](./COMMUNITIES_API.md)

### Comment Endpoints

#### Collection Endpoints
- `GET /comments/` - List all comments
  - Filtering options:
    - `?post={post_id}` - Filter by post ID
    - `?post_path={post_path}` - Filter by post path
    - `?parent={parent_id}` - Filter by parent comment ID
    - `?parent=none` - Get only top-level comments
    - `?username={username}` - Filter by username
    - `?time={day|week|month|year}` - Filter by time period
    - `?sort={new|top|controversial|hot|old}` - Sort comments

- `POST /comments/` - Create a new comment
  - Requires authentication
  - Will fail if post is locked
  - Will fail if user is banned from the community

#### Detail Endpoints
- `GET /comments/{id}/` - Get a specific comment
- `PUT /comments/{id}/` - Update a comment (owner only)
- `PATCH /comments/{id}/` - Partially update a comment (owner only)
- `DELETE /comments/{id}/` - Delete a comment (owner only)

[See all comment endpoints](./COMMENTS_API.md)

### Post Endpoints

#### Collection Endpoints
- `GET /posts/` - List all posts
  - Filtering options:
    - `?community={community_id}` - Filter by community ID
    - `?community_path={community_path}` - Filter by community path
    - `?username={username}` - Filter by username
    - `?flair={flair_id}` - Filter by flair
    - `?is_pinned={true|false}` - Filter by pinned status
    - `?time={day|week|month|year}` - Filter by time period
    - `?sort={new|hot|top|controversial}` - Sort posts

- `POST /posts/` - Create a new post
  - Requires authentication
  - Will fail if user is banned from the community

- `GET /posts/pinned/` - Get pinned posts (can be filtered by community)

#### Detail Endpoints
- `GET /posts/{path}/` - Get a specific post by path
- `PUT /posts/{path}/` - Update a post (owner only)
- `PATCH /posts/{path}/` - Partially update a post (owner only)
- `DELETE /posts/{path}/` - Delete a post (owner or moderator only)

[See all post endpoints](./POSTS_API.md)

### Search Endpoints

#### Collection Endpoints
- `GET /search/` - Search across posts, comments, communities, and users
  - Query parameters:
    - `?q={search_query}` - The search term (minimum 3 characters) 
    - `?type={all|posts|comments|communities|users}` - Filter by content type
    - `?community={community_id}` - Filter results to a specific community
    - `?sort={relevant|new|top}` - Sort search results

[See all search endpoints](./SEARCH_API.md)

### Media Upload Endpoints

- `POST /uploads/media/` - Upload an image or video file
  - Requires authentication
  - Form data parameters:
    - `file` - The image or video file to upload
    - `type` - Media context type [post|community|profile] (default: post)
  - Response:
    - `url` - URL to the uploaded media
    - `success` - Boolean indicating success
    - `media_type` - Detected media type (image or video)

### Vote Endpoints

#### Collection Endpoints
- `GET /votes/` - List all votes
  - Query parameters:
    - `?user={user_id}` - Filter by user
    - `?post={post_id}` - Filter by post
    - `?comment={comment_id}` - Filter by comment
    - `?type={up|down}` - Filter by vote type

- `POST /votes/` - Create a new vote
  - Requires authentication

[See all vote endpoints](./UPLOADS_API.md)

### Notification Endpoints

#### Collection Endpoints
- `GET /notifications/` - List user's notifications
  - Query parameters:
    - `?is_read={true|false}` - Filter by read status
    - `?type={notification_type}` - Filter by notification type

- `POST /notifications/` - Create a new notification
  - Requires authentication

- `GET /notifications/count/` - Get notification counts
  - Returns unread count and total count

- `POST /notifications/mark-all-read/` - Mark all notifications as read

#### Detail Endpoints
- `GET /notifications/{id}/` - Get a specific notification
  - Automatically marks the notification as read

[See all notification endpoints](./NOTIFICATIONS_API.md)

> **Note:** We also have a messaging system built, but it's currently buggy, so you'll have to figure it out yourself if you want to use it.

## Setup and Installation

1. Create a `.env` file in the backend folder with all values filled in:

```
# Django Settings
DEBUG=
SECRET_KEY=
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
DATABASE_URL=

# Email Settings
EMAIL_HOST=
EMAIL_PORT=
EMAIL_USE_TLS=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=

# Frontend URL
FRONTEND_URL=

# JWT Settings
JWT_SECRET_KEY=
JWT_ACCESS_TOKEN_LIFETIME=
JWT_REFRESH_TOKEN_LIFETIME=

# CORS Settings
CORS_ALLOWED_ORIGINS=

# Redis (for Channels)
REDIS_HOST=
REDIS_PORT=6379
REDIS_URL=
#RECAPTCHA_PUBLIC_KEY=
#RECAPTCHA_SECRET_KEY=

USE_BUNNY_STORAGE=
BUNNY_STORAGE_API_KEY=
BUNNY_STORAGE_ZONE=redify
BUNNY_STORAGE_REGION=de  
BUNNY_STORAGE_URL=

USE_BACKBLAZE=False
B2_BUCKET_NAME=
B2_ACCESS_KEY=
B2_SECRET_KEY=
B2_REGION=
```

2. Install all dependencies:
```
pip install -r requirements.txt
```

3. Run the application:
```
daphne reddit_clone.asgi:application
