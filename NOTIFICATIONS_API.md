# secure Thread - Notifications API Endpoints

This document describes the available API endpoints for handling user notifications in the Onuze application.

## Core Notification Endpoints

### Notification Collection Endpoints

- `GET /notifications/` - List user's notifications
  - Query parameters:
    - `?is_read={true|false}` - Filter by read status
    - `?type={notification_type}` - Filter by notification type

- `POST /notifications/` - Create a new notification
  - Requires authentication

- `GET /notifications/count/` - Get notification counts
  - Returns unread count and total count

- `POST /notifications/mark-all-read/` - Mark all notifications as read

### Notification Detail Endpoints

- `GET /notifications/{id}/` - Get a specific notification
  - Automatically marks the notification as read

- `PUT /notifications/{id}/` - Update a notification
  - Only allows changing the read status

- `PATCH /notifications/{id}/` - Partially update a notification
  - Only allows changing the read status

- `DELETE /notifications/{id}/` - Delete a notification

### Notification Actions

- `POST /notifications/{id}/mark_read/` - Mark a notification as read
- `POST /notifications/{id}/mark_unread/` - Mark a notification as unread

## Notification Data Model

### Notification
- `id` - UUID primary key
- `user` - User who receives the notification
- `sender` - User who triggered the notification (optional)
- `notification_type` - Type of notification (comment_reply, post_reply, mention, etc.)
- `content_type` - Type of content (post, comment, community, etc.)
- `content_id` - ID of the related content
- `message` - Text description of the notification
- `is_read` - Whether the notification has been read
- `created_at` - Timestamp when the notification was created
- `link_url` - URL to view the related content

## Notification Types

- `comment_reply` - When someone replies to your comment
- `post_reply` - When someone comments on your post
- `mention` - When someone mentions you with @username
- `mod_action` - When a moderator action affects you
- `vote_milestone` - When your post/comment reaches upvote milestones
- `welcome` - When you first create an account

## Features

### Real-time Notifications
Notifications are delivered in real-time via WebSockets to provide immediate feedback to users.

### Notification Aggregation
Similar notifications can be grouped to prevent overwhelming users.

### Read Status Tracking
Notifications track read/unread status to help users identify new activity.

### Notification Links
Each notification includes a direct link to the relevant content. 