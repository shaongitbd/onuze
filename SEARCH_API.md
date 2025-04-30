# SecureThread - Search API Endpoints

This document describes the available API endpoints for searching content in the SecureThread application.

## Core Search Endpoints

### Search Collection Endpoints

- `GET /search/` - Search across posts, comments, communities, and users
  - Query parameters:
    - `?q={search_query}` - The search term (minimum 3 characters) 
    - `?type={all|posts|comments|communities|users}` - Filter by content type
    - `?community={community_id}` - Filter results to a specific community
    - `?sort={relevant|new|top}` - Sort search results

### Search History Endpoints

- `GET /search/history/` - Get user's search history
  - Requires authentication

## Search Data Models

### SearchHistory
- `id` - UUID primary key
- `user` - Foreign key to the User who performed the search
- `query` - The search term used
- `created_at` - Timestamp when the search was performed
- `ip_address` - IP address of the user
- `user_agent` - Browser/client information
- `result_count` - Number of results returned

## Features

### Multi-content Search
The search API allows searching across different content types simultaneously:
- Posts (titles and content)
- Comments (content)
- Communities (names and descriptions)
- Users (usernames and bios)

### Full-text Search
- Uses PostgreSQL's full-text search capabilities
- Applies different weights to different fields:
  - Post titles have higher weight than post content
  - Community names have higher weight than descriptions

### Search Filtering
- Filter by content type to focus results
- Filter by community to search within a specific community

### Search Sorting
Results can be sorted by:
- `relevant` - Most relevant results first (default)
- `new` - Most recent results first
- `top` - Most popular results first (by votes/members) 