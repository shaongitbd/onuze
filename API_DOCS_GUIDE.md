# API Documentation Guide for Frontend Developers

This guide explains how to use the Swagger/OpenAPI documentation for frontend development with the Reddit Clone API.

## Accessing the API Documentation

The API documentation is available at two endpoints:

- **Swagger UI**: `/api/docs/` - Interactive documentation with a user-friendly interface
- **ReDoc**: `/api/redoc/` - Alternative documentation format that's easier to read

## Authentication

Before testing most endpoints, you'll need to authenticate:

1. Use the `/api/v1/auth/jwt/create/` endpoint to get a JWT token:
   ```
   POST /api/v1/auth/jwt/create/
   Content-Type: application/json
   
   {
     "username": "your_username",
     "password": "your_password"
   }
   ```

2. In the Swagger UI, click the "Authorize" button and enter:
   ```
   JWT your_access_token
   ```

3. For frontend requests, add the token to your headers:
   ```javascript
   headers: {
     'Authorization': 'JWT your_access_token'
   }
   ```

## Key Endpoints

Here are the main API endpoints for frontend development:

### User Management
- `POST /api/v1/auth/users/` - Register a new user
- `POST /api/v1/auth/jwt/create/` - Login and get tokens
- `POST /api/v1/auth/jwt/refresh/` - Refresh an expired token

### Communities
- `GET /api/v1/communities/` - List communities
- `POST /api/v1/communities/` - Create a community
- `GET /api/v1/communities/{id}/` - Get community details

### Posts
- `GET /api/v1/posts/` - List posts
- `POST /api/v1/posts/` - Create a post
- `GET /api/v1/posts/{id}/` - Get post details
- `PUT /api/v1/posts/{id}/` - Update a post
- `DELETE /api/v1/posts/{id}/` - Delete a post

### Comments
- `GET /api/v1/comments/` - List comments
- `POST /api/v1/comments/` - Create a comment
- `GET /api/v1/posts/{post_id}/comments/` - Get comments for a post

### Votes
- `POST /api/v1/votes/posts/{post_id}/vote/` - Vote on a post. Request body:
  ```json
  {
    "content_type": "post",
    "content_id": 1121, // Replace with the actual post ID
    "vote_type": 1     // 1 for upvote, -1 for downvote
  }
  ```
- `POST /api/v1/votes/comments/{comment_id}/vote/` - Vote on a comment. Request body:
  ```json
  {
    "content_type": "comment",
    "content_id": 1121, // Replace with the actual comment ID
    "vote_type": 1     // 1 for upvote, -1 for downvote
  }
  ```

### Media Uploads
- `POST /api/v1/uploads/images/` - Upload an image

## Working with Media

To upload media files:

1. Use the `/api/v1/uploads/images/` endpoint
2. Send a `multipart/form-data` request with:
   - `image`: The file to upload
   - `type`: "post", "community", or "profile"
3. Store the returned URL to use in your frontend

## Exporting API Documentation

You can get the complete API specification in OpenAPI format using one of these methods:

1. Direct URL access:
   - JSON format: `/api/docs/?format=json`
   - YAML format: `/api/docs/?format=yaml`

2. Using curl:
   ```bash
   # For JSON
   curl -X GET "http://localhost:8000/api/docs/?format=json" -o openapi.json

   # For YAML
   curl -X GET "http://localhost:8000/api/docs/?format=yaml" -o openapi.yaml
   ```

3. In Swagger UI, you can also:
   - Right-click anywhere on the page
   - Select "View Page Source"
   - Find the `spec` variable in the HTML which contains the complete OpenAPI specification

The exported specification can be used with tools like Postman, OpenAPI Generator, or to generate client libraries for your frontend.

## Best Practices

1. Use the Swagger UI to:
   - Understand available parameters
   - Test requests before implementing them
   - See response formats and status codes

2. Implement proper error handling:
   - Check HTTP status codes (2xx, 4xx, 5xx)
   - Parse error messages from the response body

3. Cache frequently accessed data:
   - Community listings
   - User profiles
   - Static content

4. Implement token refresh logic:
   - Store both access and refresh tokens
   - Automatically refresh expired access tokens

5. Use WebSockets for real-time updates instead of polling 