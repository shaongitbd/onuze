# Reddit Clone API Summary

This document provides a summarized overview of the Reddit Clone API endpoints, generated from the `swagger_api.json` file.

**Base Path:** `/api/v1`
**Host:** `localhost:8000`
**Schemes:** `http`

---

## Authentication (`auth`, `security`)

Handles user registration, login (token generation), logout, token refresh/verification, password reset, and user profile management (`/me`).

**Key Endpoints:**

*   **`POST /auth/token/`**
    *   **Description:** Login with credentials (email, password) to get HttpOnly cookies containing access/refresh tokens.
    *   **Request Body:** `TokenObtainPair` (`email`, `password`)
    *   **Response:** `TokenObtainPair` (contains tokens, but they are primarily set in cookies)
*   **`POST /auth/token/refresh/`**
    *   **Description:** Refresh access token using the refresh token from the cookie.
    *   **Request Body:** `TokenRefresh` (empty object, relies on cookie)
    *   **Response:** `TokenRefresh` (contains new access token, primarily set in cookies)
*   **`POST /auth/logout/`** (Also `POST /security/logout/`)
    *   **Description:** Logout user, clear cookies, revoke refresh token.
    *   **Response:** 201 No Content (success)
*   **`POST /auth/users/`**
    *   **Description:** Register a new user.
    *   **Request Body:** `UserCreatePasswordRetype` (`username`, `email`, `password`, `re_password`)
    *   **Response:** `UserCreatePasswordRetype` (contains user details)
*   **`GET /auth/users/me/`**
    *   **Description:** Get details of the currently authenticated user. Requires valid cookie/token.
    *   **Response:** `User` object (paginated response, but typically used to get single user)
*   **`PUT /auth/users/me/`**
    *   **Description:** Update details of the currently authenticated user.
    *   **Request Body:** `User` object (subset of fields allowed for update)
    *   **Response:** Updated `User` object
*   **`PATCH /auth/users/me/`**
    *   **Description:** Partially update details of the currently authenticated user.
    *   **Request Body:** Partial `User` object
    *   **Response:** Updated `User` object
*   **`POST /auth/users/activation/`**
    *   **Description:** Activate user account using UID and token from email.
    *   **Request Body:** `Activation` (`uid`, `token`)
*   **`POST /auth/users/resend_activation/`**
    *   **Description:** Resend activation email.
    *   **Request Body:** `SendEmailReset` (`email`)
*   **`POST /auth/users/reset_password/`**
    *   **Description:** Request password reset email.
    *   **Request Body:** `SendEmailReset` (`email`)
*   **`POST /auth/users/reset_password_confirm/`**
    *   **Description:** Confirm password reset using UID and token.
    *   **Request Body:** `PasswordResetConfirmRetype` (`uid`, `token`, `new_password`, `re_new_password`)
*   **`POST /auth/users/set_password/`**
    *   **Description:** Change password for logged-in user.
    *   **Request Body:** `SetPasswordRetype` (`new_password`, `re_new_password`, `current_password`)

*(Other `/auth/users/...` endpoints exist for email reset, etc.)*

---

## Users (`users`)

Handles general user listing, retrieving specific user details, and user-related actions like blocking.

**Key Endpoints:**

*   **`GET /users/`**
    *   **Description:** List users (brief details).
    *   **Query Params:** `limit`, `offset`
    *   **Response:** Paginated list of `UserBrief` objects.
*   **`POST /users/`**
    *   **Description:** Create a new user (alternative registration, includes captcha).
    *   **Request Body:** `UserCreate` (`username`, `email`, `password`, `password_confirmation`, `captcha`, optional `bio`, `avatar`)
    *   **Response:** `UserCreate` object.
*   **`GET /users/me/`**
    *   **Description:** Get full details of the *currently authenticated* user.
    *   **Response:** `User` object.
*   **`PUT /users/me/`**
    *   **Description:** Update *currently authenticated* user details.
    *   **Request Body:** `UserUpdate` (`username`, optional `bio`, `avatar`, `two_factor_enabled`)
    *   **Response:** `UserUpdate` object.
*   **`PATCH /users/me/`**
    *   **Description:** Partially update *currently authenticated* user details.
    *   **Request Body:** Partial `UserUpdate` object.
    *   **Response:** `UserUpdate` object.
*   **`GET /users/{id}/`**
    *   **Description:** Get full details of a specific user by ID.
    *   **Path Param:** `id` (User UUID)
    *   **Response:** `User` object.
*   **`GET /users/blocks/`**
    *   **Description:** List users blocked by the current user.
    *   **Response:** Paginated list of `UserBlock` objects.
*   **`POST /users/blocks/`**
    *   **Description:** Block a user.
    *   **Request Body:** `UserBlock` (`blocked_user_id`)
    *   **Response:** `UserBlock` object.
*   **`DELETE /users/blocks/{id}/`**
    *   **Description:** Unblock a user (using the block ID).
    *   **Path Param:** `id` (Block UUID)
    *   **Response:** 204 No Content.
*   **`POST /users/password/change/`**
    *   **Description:** Change password for the current user (alternative to `/auth/users/set_password/`).
    *   **Request Body:** `PasswordChange` (`current_password`, `new_password`, `confirm_password`)
*   **`GET /users/{id}/posts/`**
    *   **Description:** Get posts created by a specific user. *(Response schema seems incorrect in Swagger, likely returns paginated list of Posts)*
*   **`GET /users/{id}/comments/`**
    *   **Description:** Get comments created by a specific user. *(Response schema seems incorrect in Swagger, likely returns paginated list of Comments)*

*(Other endpoints for 2FA, roles exist)*

---

## Communities (`communities`)

Handles creation, listing, details, joining/leaving, moderation, rules, and flairs for communities (subreddits).

**Key Endpoints:**

*   **`GET /communities/`**
    *   **Description:** List communities.
    *   **Query Params:** `limit`, `offset`
    *   **Response:** Paginated list of `Community` objects.
*   **`POST /communities/`**
    *   **Description:** Create a new community.
    *   **Request Body:** `Community` (`name`, `description`, optional `sidebar_content`, `banner_image`, `icon_image`, `is_private`, `is_nsfw`)
    *   **Response:** `Community` object.
*   **`GET /communities/{id}/`**
    *   **Description:** Get details of a specific community.
    *   **Path Param:** `id` (Community UUID)
    *   **Response:** `Community` object.
*   **`PUT /communities/{id}/`**
    *   **Description:** Update a community.
    *   **Path Param:** `id` (Community UUID)
    *   **Request Body:** `Community` object.
    *   **Response:** `Community` object.
*   **`PATCH /communities/{id}/`**
    *   **Description:** Partially update a community.
    *   **Path Param:** `id` (Community UUID)
    *   **Request Body:** Partial `Community` object.
    *   **Response:** `Community` object.
*   **`DELETE /communities/{id}/`**
    *   **Description:** Delete a community.
    *   **Path Param:** `id` (Community UUID)
    *   **Response:** 204 No Content.
*   **`POST /communities/{id}/join/`**
    *   **Description:** Join a community.
    *   **Path Param:** `id` (Community UUID)
    *   **Response:** `Community` object (or success status).
*   **`POST /communities/{id}/leave/`**
    *   **Description:** Leave a community.
    *   **Path Param:** `id` (Community UUID)
    *   **Response:** `Community` object (or success status).
*   **`GET /communities/flairs/`**
    *   **Description:** List all flairs (requires filtering, likely by community).
    *   **Response:** Paginated list of `Flair` objects.
*   **`POST /communities/flairs/`**
    *   **Description:** Create a new flair for a community.
    *   **Request Body:** `Flair` (`community` (UUID), `name`, `background_color`, `text_color`, `is_mod_only`)
    *   **Response:** `Flair` object.
*   **`GET /communities/rules/`**
    *   **Description:** List all rules (requires filtering, likely by community).
    *   **Response:** Paginated list of `CommunityRule` objects.
*   **`POST /communities/rules/`**
    *   **Description:** Create a new rule for a community.
    *   **Request Body:** `CommunityRule` (`community` (UUID), `title`, `description`, `order`)
    *   **Response:** `CommunityRule` object.

*(Specific endpoints for managing members, moderators, individual flairs/rules also exist under `/communities/...`)*

---

## Posts (`posts`)

Handles creation, listing, details, updating, deleting, and managing posts.

**Key Endpoints:**

*   **`GET /posts/`**
    *   **Description:** List posts (filtered by community, user, etc. via query params assumed - *not explicit in Swagger*).
    *   **Query Params:** `limit`, `offset` (potential filters like `community_id`, `user_id` are standard practice but not listed)
    *   **Response:** Paginated list of `Post` objects.
*   **`POST /posts/`**
    *   **Description:** Create a new post.
    *   **Request Body:** `Post` (`community_id`, `title`, `content`, optional `flair_id`, `is_nsfw`, `is_spoiler`)
    *   **Response:** `Post` object.
*   **`GET /posts/{id}/`**
    *   **Description:** Get details of a specific post.
    *   **Path Param:** `id` (Post UUID)
    *   **Response:** `Post` object.
*   **`PUT /posts/{id}/`**
    *   **Description:** Update a post.
    *   **Path Param:** `id` (Post UUID)
    *   **Request Body:** `Post` object.
    *   **Response:** `Post` object.
*   **`PATCH /posts/{id}/`**
    *   **Description:** Partially update a post.
    *   **Path Param:** `id` (Post UUID)
    *   **Request Body:** Partial `Post` object.
    *   **Response:** `Post` object.
*   **`DELETE /posts/{id}/`**
    *   **Description:** Delete a post.
    *   **Path Param:** `id` (Post UUID)
    *   **Response:** 204 No Content.
*   **`POST /posts/{id}/lock/`**
    *   **Description:** Lock a post.
    *   **Path Param:** `id` (Post UUID)
*   **`POST /posts/{id}/unlock/`**
    *   **Description:** Unlock a post.
    *   **Path Param:** `id` (Post UUID)
*   **`POST /posts/{id}/pin/`**
    *   **Description:** Pin a post.
    *   **Path Param:** `id` (Post UUID)
*   **`POST /posts/{id}/unpin/`**
    *   **Description:** Unpin a post.
    *   **Path Param:** `id` (Post UUID)
*   **`GET /posts/media/`**
    *   **Description:** List post media items.
    *   **Response:** Paginated list of `PostMedia` objects.
*   **`POST /posts/media/`**
    *   **Description:** Create a post media item (likely associating pre-uploaded media).
    *   **Request Body:** `PostMedia` (`post` (UUID), `media_type`, `media_url`, `thumbnail_url`, `order`)
    *   **Response:** `PostMedia` object.

---

## Comments (`comments`)

Handles creation, listing, retrieval, updating, and deleting comments.

**Key Endpoints:**

*   **`GET /comments/`**
    *   **Description:** List comments (filtered by post etc. via query params assumed - *not explicit in Swagger*).
    *   **Query Params:** `limit`, `offset` (potential filter `post_id` is standard practice but not listed)
    *   **Response:** Paginated list of `Comment` objects.
*   **`POST /comments/`**
    *   **Description:** Create a new comment.
    *   **Request Body:** `Comment` (`post` (UUID), `content`, optional `parent` (UUID for reply))
    *   **Response:** `Comment` object.
*   **`GET /comments/{id}/`**
    *   **Description:** Get details of a specific comment.
    *   **Path Param:** `id` (Comment UUID)
    *   **Response:** `Comment` object.
*   **`PUT /comments/{id}/`**
    *   **Description:** Update a comment.
    *   **Path Param:** `id` (Comment UUID)
    *   **Request Body:** `Comment` object.
    *   **Response:** `Comment` object.
*   **`PATCH /comments/{id}/`**
    *   **Description:** Partially update a comment.
    *   **Path Param:** `id` (Comment UUID)
    *   **Request Body:** Partial `Comment` object.
    *   **Response:** `Comment` object.
*   **`DELETE /comments/{id}/`**
    *   **Description:** Delete a comment.
    *   **Path Param:** `id` (Comment UUID)
    *   **Response:** 204 No Content.
*   **`POST /comments/{id}/remove/`**
    *   **Description:** Mark a comment as removed (moderator action).
    *   **Path Param:** `id` (Comment UUID)
*   **`POST /comments/{id}/restore/`**
    *   **Description:** Restore a removed comment (moderator action).
    *   **Path Param:** `id` (Comment UUID)

---

## Votes (`votes`)

Handles casting votes on posts and comments.

**Key Endpoints:**

*   **`POST /votes/`**
    *   **Description:** Cast a vote.
    *   **Request Body:** `Vote` (`content_type` ("post" or "comment"), `content_id` (UUID), `vote_type` (1 for upvote, -1 for downvote))
    *   **Response:** `Vote` object.
*   **`POST /votes/posts/{post_id}/vote/`**
    *   **Description:** Vote on a specific post (alternative endpoint).
    *   **Path Param:** `post_id` (Post UUID)
    *   **Request Body:** `Vote` (`vote_type`)
*   **`POST /votes/comments/{comment_id}/vote/`**
    *   **Description:** Vote on a specific comment (alternative endpoint).
    *   **Path Param:** `comment_id` (Comment UUID)
    *   **Request Body:** `Vote` (`vote_type`)
*   **`DELETE /votes/{id}/`**
    *   **Description:** Remove/cancel a vote (using the vote ID).
    *   **Path Param:** `id` (Vote UUID)
    *   **Response:** 204 No Content.

*(Simplified endpoints like `/votes/upvote_post/`, `/votes/downvote_post/` also exist but might be less flexible)*

---

## Uploads (`uploads`)

Handles media uploads.

**Key Endpoints:**

*   **`POST /uploads/images/`**
    *   **Description:** Upload an image file.
    *   **Request Type:** `multipart/form-data`
    *   **Form Data:** `image` (file), `type` ("post", "community", "profile" - optional, default "post")
    *   **Response:** `{ "url": "...", "success": true }`

---

## Search (`search`)

Handles searching content and viewing search history.

**Key Endpoints:**

*   **`GET /search/`**
    *   **Description:** Perform a search query.
    *   **Query Params:** `limit`, `offset`, `query` (search term), `type` ("post", "comment", "community", "user" - *assumed, not explicit*)
    *   **Response:** `SearchResult` object containing lists of results for each type.
*   **`GET /search/history/`**
    *   **Description:** View the current user's search history.
    *   **Response:** Paginated list of `SearchHistory` objects.

---

## Messages (`messages`)

Handles private messaging between users.

**Key Endpoints:**

*   **`GET /messages/`**
    *   **Description:** List messages (inbox/sent filtering likely needed via query params).
    *   **Response:** Paginated list of `PrivateMessage` objects.
*   **`POST /messages/`**
    *   **Description:** Send a private message.
    *   **Request Body:** `PrivateMessage` (`recipient_id` (UUID), `subject`, `content`)
    *   **Response:** `PrivateMessage` object.
*   **`GET /messages/{id}/`**
    *   **Description:** Retrieve a specific message (marks as read).
    *   **Path Param:** `id` (Message UUID)
    *   **Response:** `PrivateMessage` object.
*   **`DELETE /messages/{id}/`**
    *   **Description:** Delete a message.
    *   **Path Param:** `id` (Message UUID)
    *   **Response:** 204 No Content.
*   **`GET /messages/conversations/{user_id}/`**
    *   **Description:** Get the message history between the current user and another user.
    *   **Path Param:** `user_id` (User UUID)
    *   **Response:** Paginated list of `PrivateMessage` objects.
*   **`GET /messages/unread-count/`**
    *   **Description:** Get the count of unread messages.
    *   **Response:** Object containing `unread_count`.

---

## Notifications (`notifications`)

Handles user notifications.

**Key Endpoints:**

*   **`GET /notifications/`**
    *   **Description:** List user notifications.
    *   **Response:** Paginated list of `Notification` objects.
*   **`GET /notifications/count/`**
    *   **Description:** Get counts of notifications (total/unread).
    *   **Response:** `NotificationCount` object.
*   **`POST /notifications/mark-all-read/`**
    *   **Description:** Mark all notifications as read.
    *   **Response:** 201 No Content.
*   **`POST /notifications/{id}/mark_read/`**
    *   **Description:** Mark a specific notification as read.
    *   **Path Param:** `id` (Notification UUID)
*   **`POST /notifications/{id}/mark_unread/`**
    *   **Description:** Mark a specific notification as unread.
    *   **Path Param:** `id` (Notification UUID)

---

## Moderation (`moderation`)

Handles reports and ban appeals.

**Key Endpoints:**

*   **`GET /moderation/reports/`**
    *   **Description:** List reports (requires mod/admin permissions).
    *   **Response:** Paginated list of `Report` objects.
*   **`POST /moderation/reports/`**
    *   **Description:** Create a report for a post, comment, or user.
    *   **Request Body:** `Report` (`content_type`, `content_id`, `reason`, `details`)
    *   **Response:** `Report` object.
*   **`GET /moderation/ban-appeals/`**
    *   **Description:** List ban appeals (requires mod/admin permissions).
    *   **Response:** Paginated list of `BanAppeal` objects.
*   **`POST /moderation/ban-appeals/`**
    *   **Description:** Create a ban appeal.
    *   **Request Body:** `BanAppeal` (`appeal_type`, `reason`, `evidence`, optional `community`)
    *   **Response:** `BanAppeal` object.

*(Specific endpoints for managing/resolving reports and appeals exist)*

---

## Definitions (Key Objects)

*(Brief overview of some common data structures)*

*   **UserBrief:** `id`, `username`, `avatar`, `karma`
*   **User:** Extends `UserBrief` + `email`, `date_joined`, `last_login`, `bio`, `is_verified`, `is_staff`, `two_factor_enabled`
*   **Community:** `id`, `name`, `description`, `created_at`, `created_by`, `sidebar_content`, `banner_image`, `icon_image`, `is_private`, `member_count`, `is_nsfw`
*   **Post:** `id`, `user` (UserBrief), `community` (Community), `community_id`, `title`, `content`, `created_at`, `updated_at`, `is_edited`, `is_deleted`, `is_locked`, `is_pinned`, `flair` (Flair), `flair_id`, `upvote_count`, `downvote_count`, `comment_count`, `view_count`, `is_nsfw`, `is_spoiler`, `media` (list of PostMedia), `score`
*   **Comment:** `id`, `post` (UUID), `user` (UserBrief), `parent` (UUID), `content`, `created_at`, `updated_at`, `is_edited`, `is_deleted`, `upvote_count`, `downvote_count`, `score`, `path`, `depth`, `reply_count`
*   **Vote:** `id`, `user_id`, `username`, `content_type`, `content_id`, `vote_type`, `created_at`, `updated_at`
*   **TokenObtainPair:** `email`, `password` (request); `access`, `refresh` (response, usually in cookies)
*   **UserCreatePasswordRetype:** `username`, `email`, `password`, `re_password` 