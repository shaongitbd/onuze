# Reddit Clone Database Schema

## Core Tables

### 1. User
- `id` (PK): UUID
- `username`: VARCHAR(150), unique
- `email`: VARCHAR(255), unique
- `password`: VARCHAR(255), hashed
- `date_joined`: TIMESTAMP
- `last_login`: TIMESTAMP
- `is_active`: BOOLEAN
- `is_verified`: BOOLEAN
- `is_staff`: BOOLEAN (admin access)
- `bio`: TEXT, nullable
- `avatar`: VARCHAR(255), nullable (path to image)
- `karma`: INTEGER, default 0
- `two_factor_enabled`: BOOLEAN, default false
- `failed_login_attempts`: INTEGER, default 0
- `last_failed_login`: TIMESTAMP, nullable
- `account_locked_until`: TIMESTAMP, nullable
- `is_site_banned`: BOOLEAN, default false
- `site_ban_reason`: TEXT, nullable
- `site_banned_until`: TIMESTAMP, nullable
- `site_banned_by_id` (FK): References User, nullable

### 2. Role
- `id` (PK): UUID
- `name`: VARCHAR(50), unique (e.g., "User", "Moderator", "Admin")
- `description`: TEXT

### 3. UserRole
- `id` (PK): UUID
- `user_id` (FK): References User
- `role_id` (FK): References Role
- `created_at`: TIMESTAMP
- `created_by_id` (FK): References User (who assigned the role)

### 4. Community (Subreddit)
- `id` (PK): UUID
- `name`: VARCHAR(100), unique
- `description`: TEXT
- `created_at`: TIMESTAMP
- `created_by_id` (FK): References User
- `sidebar_content`: TEXT, nullable
- `banner_image`: VARCHAR(255), nullable (path to image)
- `icon_image`: VARCHAR(255), nullable (path to image)
- `is_private`: BOOLEAN, default false
- `member_count`: INTEGER, default 0
- `is_nsfw`: BOOLEAN, default false

### 5. CommunityMember
- `id` (PK): UUID
- `community_id` (FK): References Community
- `user_id` (FK): References User
- `joined_at`: TIMESTAMP
- `is_banned`: BOOLEAN, default false
- `ban_reason`: TEXT, nullable
- `banned_until`: TIMESTAMP, nullable
- `banned_by_id` (FK): References User, nullable

### 6. CommunityModerator
- `id` (PK): UUID
- `community_id` (FK): References Community
- `user_id` (FK): References User
- `appointed_at`: TIMESTAMP
- `appointed_by_id` (FK): References User
- `permissions`: JSONB (e.g., {"can_ban_users": true, "can_edit_posts": true})

### 7. CommunityRule
- `id` (PK): UUID
- `community_id` (FK): References Community
- `title`: VARCHAR(100)
- `description`: TEXT, nullable
- `created_at`: TIMESTAMP
- `created_by_id` (FK): References User
- `order`: INTEGER (for display order)

### 8. Post
- `id` (PK): UUID
- `community_id` (FK): References Community
- `user_id` (FK): References User
- `title`: VARCHAR(300)
- `content`: TEXT
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP, nullable
- `is_edited`: BOOLEAN, default false
- `is_deleted`: BOOLEAN, default false
- `is_locked`: BOOLEAN, default false
- `locked_by_id` (FK): References User, nullable
- `locked_reason`: TEXT, nullable
- `is_pinned`: BOOLEAN, default false
- `flair_id` (FK): References Flair, nullable
- `upvote_count`: INTEGER, default 0
- `downvote_count`: INTEGER, default 0
- `comment_count`: INTEGER, default 0
- `view_count`: INTEGER, default 0
- `is_nsfw`: BOOLEAN, default false
- `is_spoiler`: BOOLEAN, default false

### 9. PostMedia
- `id` (PK): UUID
- `post_id` (FK): References Post
- `media_type`: VARCHAR(50) (e.g., "image", "video", "gif")
- `media_url`: VARCHAR(255) (path to media)
- `thumbnail_url`: VARCHAR(255), nullable
- `order`: INTEGER (for display order if multiple media)
- `created_at`: TIMESTAMP

### 10. Comment
- `id` (PK): UUID
- `post_id` (FK): References Post
- `user_id` (FK): References User
- `parent_id` (FK): References Comment, nullable (for nested comments)
- `content`: TEXT
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP, nullable
- `is_edited`: BOOLEAN, default false
- `is_deleted`: BOOLEAN, default false
- `upvote_count`: INTEGER, default 0
- `downvote_count`: INTEGER, default 0
- `path`: VARCHAR(255) (materialized path for efficient tree traversal)
- `depth`: INTEGER (nesting level)

### 11. Vote
- `id` (PK): UUID
- `user_id` (FK): References User
- `content_type`: VARCHAR(50) (e.g., "post", "comment")
- `content_id`: UUID (polymorphic reference to Post or Comment)
- `vote_type`: SMALLINT (-1 for downvote, +1 for upvote)
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP, nullable

### 12. Flair
- `id` (PK): UUID
- `community_id` (FK): References Community
- `name`: VARCHAR(100)
- `background_color`: VARCHAR(7) (hex color)
- `text_color`: VARCHAR(7) (hex color)
- `created_at`: TIMESTAMP
- `created_by_id` (FK): References User
- `is_mod_only`: BOOLEAN, default false

### 13. Notification
- `id` (PK): UUID
- `user_id` (FK): References User (recipient)
- `sender_id` (FK): References User, nullable
- `notification_type`: VARCHAR(50) (e.g., "comment_reply", "post_reply", "mention", "mod_action")
- `content_type`: VARCHAR(50) (e.g., "post", "comment", "message")
- `content_id`: UUID (polymorphic reference)
- `message`: TEXT
- `is_read`: BOOLEAN, default false
- `created_at`: TIMESTAMP
- `link_url`: VARCHAR(255), nullable (app URL to navigate to)

### 14. Report
- `id` (PK): UUID
- `reporter_id` (FK): References User
- `content_type`: VARCHAR(50) (e.g., "post", "comment", "user")
- `content_id`: UUID (polymorphic reference)
- `reason`: VARCHAR(100)
- `details`: TEXT, nullable
- `created_at`: TIMESTAMP
- `status`: VARCHAR(50) (e.g., "pending", "resolved", "rejected")
- `resolved_by_id` (FK): References User, nullable
- `resolved_at`: TIMESTAMP, nullable
- `resolution_notes`: TEXT, nullable
- `community_id` (FK): References Community

### 15. PrivateMessage
- `id` (PK): UUID
- `sender_id` (FK): References User
- `recipient_id` (FK): References User
- `subject`: VARCHAR(255)
- `content`: TEXT
- `created_at`: TIMESTAMP
- `is_read`: BOOLEAN, default false
- `read_at`: TIMESTAMP, nullable
- `is_deleted_by_sender`: BOOLEAN, default false
- `is_deleted_by_recipient`: BOOLEAN, default false

### 16. UserBlock
- `id` (PK): UUID
- `user_id` (FK): References User (who is blocking)
- `blocked_user_id` (FK): References User (who is blocked)
- `created_at`: TIMESTAMP
- `reason`: TEXT, nullable

### 17. UserSession
- `id` (PK): UUID
- `user_id` (FK): References User
- `token`: VARCHAR(255), unique
- `ip_address`: VARCHAR(45), nullable
- `user_agent`: TEXT, nullable
- `device_info`: JSONB, nullable
- `created_at`: TIMESTAMP
- `expires_at`: TIMESTAMP
- `last_activity`: TIMESTAMP

## Security and Authentication Tables

### 18. RefreshToken
- `id` (PK): UUID
- `user_id` (FK): References User
- `token`: VARCHAR(255), unique
- `created_at`: TIMESTAMP
- `expires_at`: TIMESTAMP
- `revoked`: BOOLEAN, default false
- `revoked_at`: TIMESTAMP, nullable
- `issued_by_ip`: VARCHAR(45), nullable

### 19. EmailVerification
- `id` (PK): UUID
- `user_id` (FK): References User
- `token`: VARCHAR(255), unique
- `created_at`: TIMESTAMP
- `expires_at`: TIMESTAMP
- `verified_at`: TIMESTAMP, nullable
- `is_verified`: BOOLEAN, default false

### 20. PasswordReset
- `id` (PK): UUID
- `user_id` (FK): References User
- `token`: VARCHAR(255), unique
- `created_at`: TIMESTAMP
- `expires_at`: TIMESTAMP
- `used_at`: TIMESTAMP, nullable
- `is_used`: BOOLEAN, default false
- `requested_ip`: VARCHAR(45), nullable

### 21. AuditLog
- `id` (PK): UUID
- `user_id` (FK): References User, nullable
- `action`: VARCHAR(100)
- `entity_type`: VARCHAR(50)
- `entity_id`: UUID, nullable
- `ip_address`: VARCHAR(45), nullable
- `user_agent`: TEXT, nullable
- `details`: JSONB, nullable
- `created_at`: TIMESTAMP

### 22. RateLimit
- `id` (PK): UUID
- `user_id` (FK): References User, nullable (for anonymous rate limiting)
- `ip_address`: VARCHAR(45), nullable
- `endpoint`: VARCHAR(255) 
- `request_count`: INTEGER, default 1
- `first_request`: TIMESTAMP
- `last_request`: TIMESTAMP
- `expires_at`: TIMESTAMP

### 23. BanAppeal
- `id` (PK): UUID
- `user_id` (FK): References User (who is appealing)
- `appeal_type`: VARCHAR(50) (e.g., "community_ban", "site_ban")
- `community_id` (FK): References Community, nullable (if community ban)
- `reason`: TEXT (user's explanation for appeal)
- `evidence`: TEXT, nullable (any evidence user provides)
- `status`: VARCHAR(50) (e.g., "pending", "approved", "rejected")
- `created_at`: TIMESTAMP
- `reviewed_at`: TIMESTAMP, nullable
- `reviewed_by_id` (FK): References User, nullable (admin/mod who reviewed)
- `reviewer_notes`: TEXT, nullable (private notes for review decision)
- `response_to_user`: TEXT, nullable (explanation sent to user)
- `original_ban_reason`: TEXT, nullable (for reference)
- `original_banned_until`: TIMESTAMP, nullable (for reference)

## Indexes & Constraints

- Add indexes on all foreign keys
- Add unique constraints on username, email
- Add composite unique constraints where needed (e.g., user_id + community_id in CommunityMember)
- Add partial indexes for common queries (e.g., is_deleted=false)
- Add text search indexes for search functionality

## Notes

1. Use UUIDs as primary keys to avoid enumeration attacks
2. Keep sensitive data encrypted at rest
3. Implement row-level security policies in PostgreSQL
4. Consider using schema partitioning for high-volume tables (e.g., Vote, Comment)
5. Add appropriate triggers for:
   - Updating comment_count on Post
   - Updating karma scores on User
   - Updating member_count on Community
   - Maintaining materialized paths in Comment
6. Use database transactions for operations affecting multiple tables
7. Implement appropriate cascade rules for deletes
8. Consider using JSON/JSONB for flexible data without the need for schema migrations
9. Implement proper database-level constraints for data integrity
10. Ban management:
    - Community moderators can ban users from communities (see CommunityMember table)
    - Admins can ban users site-wide (see User table `is_site_banned` field)
    - Both ban types support temporary bans with expiration dates
    - Users can appeal either type of ban through the BanAppeal system
    - For community bans, moderators review appeals; for site bans, admins review
    - Appeal outcomes are tracked with status, reviewer notes, and responses to users 