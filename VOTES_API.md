# Onuze - Votes API Endpoints

This document describes the available API endpoints for voting on content in the Onuze application.

## Core Vote Endpoints

### Vote Collection Endpoints

- `GET /votes/` - List all votes
  - Query parameters:
    - `?user={user_id}` - Filter by user
    - `?post={post_id}` - Filter by post
    - `?comment={comment_id}` - Filter by comment
    - `?type={up|down}` - Filter by vote type

- `POST /votes/` - Create a new vote
  - Requires authentication

### Vote Detail Endpoints

- `GET /votes/{id}/` - Get a specific vote
- `PUT /votes/{id}/` - Update a vote (change vote type)
- `DELETE /votes/{id}/` - Remove a vote

### Simplified Voting Endpoints

- `POST /posts/{post_path}/vote/` - Vote on a post using its path
  - Requires authentication
  - Request body: `{"vote_type": 1}` for upvote, `{"vote_type": -1}` for downvote

- `POST /posts/by-id/{post_id}/vote/` - Vote on a post using its ID (legacy)
  - Requires authentication
  - Request body: `{"vote_type": 1}` for upvote, `{"vote_type": -1}` for downvote

- `POST /comments/{comment_id}/vote/` - Vote on a comment
  - Requires authentication
  - Request body: `{"vote_type": 1}` for upvote, `{"vote_type": -1}` for downvote

## Vote Data Model

### Vote
- `id` - UUID primary key
- `user` - Foreign key to the User who cast the vote
- `content_type` - Type of content being voted on (post or comment)
- `content_id` - ID of the content being voted on
- `vote_type` - Type of vote (1 for upvote, -1 for downvote)
- `created_at` - Timestamp when the vote was cast
- `updated_at` - Timestamp when the vote was last updated

## Features

### Vote Types
- Upvote (+1) - Indicates approval or agreement with content
- Downvote (-1) - Indicates disapproval or disagreement with content

### Vote Tracking
- Each user can have only one active vote per content item
- Changing vote type (e.g., from upvote to downvote) updates the existing vote
- Deleting a vote removes its effect

### Vote Impact
- Updates content item's upvote/downvote counts
- Affects post/comment ranking in various sorting algorithms
- Contributes to user karma scores
- Triggers notifications for vote milestones (10, 50, 100, 500, 1000 upvotes)

### Idempotent Voting
The simplified voting endpoints are idempotent:
- Submitting the same vote type twice has no additional effect
- Submitting a different vote type changes the existing vote
- Submitting a null vote type removes an existing vote 