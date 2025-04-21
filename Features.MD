This application is a modern, secure, and scalable social platform inspired by Reddit, built with Django, Django Rest Framework, Django Channels, and React.

🚀 Core Features
1. User Authentication & Security
JWT Authentication with HttpOnly, Secure cookies
Two-Factor Authentication (2FA)
Email verification required for all users
Strong password policy and account lockout after failed attempts
Session management: Invalidate sessions on logout or password change

2. User Roles & Permissions
Role-based access: User, Moderator, Admin
Object-level permissions: Only owners can edit/delete their content
Moderator tools: Remove posts/comments, ban users

3. Subreddits (Communities)
Create, join, and browse topic-based communities
Community moderation and rules

4. Posts
Create, read, update, and delete posts
Rich text support (with safe HTML sanitization)
Image/file uploads (with type/size validation and malware scanning)
Post sorting: Hot, New, Top, Controversial
adding flare to post of community allows it.

5. Comments
Threaded/nested comments for discussions
Edit(provide security so that on edit it can modify to suspecision code /etc) and delete your own comments (verify correctly that the https reqest has not been altered)
Live updates for new comments
picture & emojis support in comments.(Handle very carefully in backend )

6. Voting System
Upvote/downvote posts and comments
Real-time vote count updates
One vote per user per item
7. Notifications
Real-time notifications for replies, mentions, and votes
Notification center for unread/read management
8. Search & Discovery
Full-text search for posts, comments, and users
Trending posts and communities

9. User Profiles
Customizable profiles with bio and avatar
View user’s posts, comments, and karma
private messages.



10. Moderation & Reporting
Report posts/comments for abuse or spam
Moderator dashboard for handling reports and user bans


🛡️ Admins vs. Moderators: Key Differences
Admin (Administrator)
Highest level of access in the system.
Full control over the entire platform, including all users, all communities, and all data.
Responsibilities:
Manage site-wide settings and configurations.
Create, edit, or delete any community (subreddit).
Manage all users, including moderators.
Access and manage all content (posts, comments, files).
Assign or remove moderator/admin roles.
View and manage system logs, analytics, and security settings.
Deploy updates, manage backups, and perform maintenance.
Analogy: Like a superuser or site owner.
Moderator:
Limited, community-specific access.
Control over one or more specific communities (subreddits).
Responsibilities:
Enforce community rules within their assigned subreddit(s).
Remove or edit posts and comments within their community.
Ban or mute users from their community.
Approve or reject posts/comments in moderation queues.
Handle user reports for their community.
Cannot:
Change site-wide settings.
Manage users or content outside their assigned communities.
Assign or remove admin roles.
Analogy: Like a forum or group manager.
add flairs to community for posting

Real-Time Features
Live updates for new posts, comments, and votes using WebSockets
Instant notifications for user interactions




Pagination:
make sure comes with inifite scrolling for posts,comments etc with higest security on backend.


Code:
Make sure the codebase is as easily understandable as possible use simpiler more lines of codes to do same thing. instead of putting comment every line write comment before function.