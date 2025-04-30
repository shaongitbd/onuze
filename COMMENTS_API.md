# Reddit Clone - Comments API Endpoints

This document describes the available API endpoints for managing comments in the SecureThread backend.

## Core Comment Endpoints

### Comment Collection Endpoints

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

### Comment Detail Endpoints

- `GET /comments/{id}/` - Get a specific comment
- `PUT /comments/{id}/` - Update a comment (owner only)
- `PATCH /comments/{id}/` - Partially update a comment (owner only)
- `DELETE /comments/{id}/` - Delete a comment (owner only)

### Comment Actions

- `POST /comments/{id}/remove/` - Moderator removal of a comment
  - Requires moderator permissions for the community
  - Marks the comment as removed, but doesn't delete the record

- `POST /comments/{id}/restore/` - Restore a removed comment
  - Requires moderator permissions for the community

## Comment Data Model

### Comment
- `id` - UUID primary key
- `post` - Foreign key to the Post the comment is on
- `user` - Foreign key to the User who created the comment
- `parent` - Foreign key to the parent Comment (null for top-level comments)
- `content` - Text content of the comment
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp (null if never updated)
- `is_edited` - Whether the comment has been edited
- `is_deleted` - Whether the comment has been deleted/removed
- `upvote_count` - Number of upvotes
- `downvote_count` - Number of downvotes
- `reply_count` - Number of direct replies to this comment
- `path` - Materialized path for efficient tree traversal
- `depth` - Nesting level of the comment

## Features

### Threaded Comments
The API supports threaded comments with unlimited nesting depth. The materialized path in the database enables efficient tree traversal and proper sorting.

### Real-time Updates
Comment creation and updates are broadcast in real-time to users viewing the same post using WebSockets.

### Notifications
When a comment is created:
- The post author receives a notification for top-level comments
- The parent comment author receives a notification for replies
- Users mentioned with `@username` receive notifications

### Sorting Options
Comments can be sorted by:
- `new` - Most recent first (default)
- `old` - Oldest first
- `top` - Highest scores first
- `controversial` - Comments with similar up/down votes
- `hot` - Higher scores with recency factor

### Soft Deletion
Comments are soft-deleted (marked as `is_deleted=True`) rather than physically removed from the database, preserving the comment tree structure. 