# Onuze - Communities API Endpoints

This document describes the available API endpoints for managing communities (subreddits) in  SecureThread .

## Core Community Endpoints

### Community Collection Endpoints

- `GET /communities/` - List all communities
- `POST /communities/` - Create a new community
- `GET /communities/popular/` - Get the top 5 communities based on member count

### Community Detail Endpoints

- `GET /communities/{path}/` - Get community details by path
- `PUT /communities/{path}/` - Update a community (owner only)
- `PATCH /communities/{path}/` - Partially update a community (owner only)
- `DELETE /communities/{path}/` - Delete a community (owner only)

### Community Membership

- `POST /communities/{path}/join/` - Join a community
- `POST /communities/{path}/leave/` - Leave a community
- `GET /communities/{path}/members/` - List all members of a community
- `GET /communities/{path}/check-ban-status/` - Check if the authenticated user is banned

### Community Moderation

- `GET /communities/{path}/moderators/` - List all moderators of a community
- `POST /communities/{path}/moderators/transfer-ownership/` - Transfer community ownership
- `GET /communities/{path}/settings/` - List community settings
- `GET /communities/{path}/banned-users/` - List banned users in the community

## Nested Community Resources

### Community Members

- `GET /communities/{path}/members/` - List all members
- `POST /communities/{path}/members/` - Add a member (moderator only)
- `GET /communities/{path}/members/{username}/` - Get a specific member
- `PUT /communities/{path}/members/{username}/` - Update a member (moderator only)
- `DELETE /communities/{path}/members/{username}/` - Remove a member (moderator only)
- `POST /communities/{path}/members/{username}/approve/` - Approve a pending member
- `POST /communities/{path}/members/{username}/ban/` - Ban a member
- `POST /communities/{path}/members/{username}/unban/` - Unban a member
- `POST /communities/{path}/members/{username}/reject/` - Reject a pending member

### Ban Management

- `POST /communities/{path}/ban/{username}/` - Ban a user from the community
- `POST /communities/{path}/unban/{username}/` - Unban a user from the community
- `GET /communities/{path}/banned/` - List banned users
- `GET /communities/{path}/ban-status/` - Check current user's ban status
- `GET /communities/{path}/users/{username}/ban-status/` - Check a specific user's ban status

### Community Moderators

- `GET /communities/{path}/moderators/` - List all moderators
- `POST /communities/{path}/moderators/` - Add a moderator (owner only)
- `GET /communities/{path}/moderators/{pk}/` - Get a specific moderator
- `PUT /communities/{path}/moderators/{pk}/` - Update a moderator (owner only)
- `DELETE /communities/{path}/moderators/{pk}/` - Remove a moderator (owner only)

### Community Rules

- `GET /communities/{path}/rules/` - List all rules
- `POST /communities/{path}/rules/` - Create a rule (moderator only)
- `GET /communities/{path}/rules/{pk}/` - Get a specific rule
- `PUT /communities/{path}/rules/{pk}/` - Update a rule (moderator only)
- `DELETE /communities/{path}/rules/{pk}/` - Delete a rule (moderator only)

### Community Flairs

- `GET /communities/{path}/flairs/` - List all flairs
- `POST /communities/{path}/flairs/` - Create a flair (moderator only)
- `GET /communities/{path}/flairs/{pk}/` - Get a specific flair
- `PUT /communities/{path}/flairs/{pk}/` - Update a flair (moderator only)
- `DELETE /communities/{path}/flairs/{pk}/` - Delete a flair (moderator only)

## Data Models

### Community
- `id` - UUID primary key
- `name` - Community name (unique, lowercase a-z only)
- `path` - URL slug for the community (auto-generated from name)
- `description` - Community description
- `created_at` - Creation timestamp
- `created_by` - User who created the community
- `sidebar_content` - Content for the community sidebar
- `banner_image` - URL to banner image
- `icon_image` - URL to icon image
- `is_private` - Whether the community is private
- `is_restricted` - Whether posting is restricted to approved users
- `member_count` - Number of members
- `is_nsfw` - Whether the community is NSFW

### CommunityMember
- Represents a user's membership in a community
- Includes fields for approval status and ban information

### CommunityModerator
- Represents a user who has moderation permissions in a community
- Tracks ownership status and specific permissions

### CommunityRule
- Rules defined for a community

### Flair
- Custom tags that can be applied to posts in a community
- Includes customization options for colors

### CommunitySetting
- Key-value storage for community-specific settings 