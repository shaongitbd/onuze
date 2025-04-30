# Reddit Clone - Posts API Endpoints

This document describes the available API endpoints for managing posts in the SecureThread application.

## Core Post Endpoints

### Post Collection Endpoints

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

### Post Detail Endpoints

- `GET /posts/{path}/` - Get a specific post by path
- `PUT /posts/{path}/` - Update a post (owner only)
- `PATCH /posts/{path}/` - Partially update a post (owner only)
- `DELETE /posts/{path}/` - Delete a post (owner or moderator only)

### Post Moderation Actions

- `POST /posts/{path}/lock/` - Lock a post to prevent new comments
  - Requires moderator permissions for the community

- `POST /posts/{path}/unlock/` - Unlock a post to allow new comments
  - Requires moderator permissions for the community

- `POST /posts/{path}/pin/` - Pin a post to the top of the community
  - Requires moderator permissions for the community

- `POST /posts/{path}/unpin/` - Unpin a post from the top of the community
  - Requires moderator permissions for the community

## Post Media Endpoints

- `GET /posts/media/` - List all post media
- `DELETE /posts/media/{id}/` - Delete a specific media item (owner only)

## Post Data Models

### Post
- `id` - UUID primary key
- `community` - Foreign key to the Community it belongs to
- `user` - Foreign key to the User who created the post
- `title` - Post title (max length 300)
- `path` - URL slug for the post (auto-generated from title)
- `content` - Text content of the post (can be null if media attached)
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp (null if never updated)
- `is_edited` - Whether the post has been edited
- `is_deleted` - Whether the post has been deleted/removed
- `is_locked` - Whether comments are disabled on the post
- `locked_by` - User who locked the post (moderator)
- `locked_reason` - Reason for locking the post
- `is_pinned` - Whether the post is pinned to top of community
- `flair` - Foreign key to the Flair assigned to the post
- `upvote_count` - Number of upvotes
- `downvote_count` - Number of downvotes
- `comment_count` - Number of comments
- `view_count` - Number of views
- `is_nsfw` - Whether the post is not safe for work
- `is_spoiler` - Whether the post contains spoilers

### PostMedia
- `id` - UUID primary key
- `post` - Foreign key to the Post it belongs to
- `media_type` - Type of media (image, video)
- `media_url` - URL to the media file
- `thumbnail_url` - URL to the thumbnail (if applicable)
- `order` - Display order for multiple media items

### Vote
- Represents a user's vote on a post
- Each user can have only one vote per post (upvote or downvote)

### PostSave
- Represents a user saving a post for later

## Features

### Sorting Options
Posts can be sorted by:
- `new` - Most recent first (default)
- `hot` - Higher scores with recency factor
- `top` - Highest scores first
- `controversial` - Posts with similar up/down votes

### Media Attachments
Posts can have multiple media attachments (images, videos).

### Real-time Updates
Posts have WebSocket consumers for real-time updates.

### Notifications
Users mentioned with `@username` in post content receive notifications.

### Soft Deletion
Posts are soft-deleted (marked as `is_deleted=True`) rather than physically removed from the database. 