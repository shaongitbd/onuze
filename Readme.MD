<div align="center">
  <img src="https://onuze.me/logo.png" alt="Onuze" width="180">
  
  # Onuze

  <p>A modern community platform with real-time interactions</p>

  [![Website](https://img.shields.io/badge/Website-onuze.me-FF424D)](https://onuze.me)
  [![License](https://img.shields.io/badge/License-CC_BY_NC_4.0-lightgrey)](#license)
  [![Django](https://img.shields.io/badge/Backend-Django-092E20)](https://www.djangoproject.com/)
  [![Next.js](https://img.shields.io/badge/Frontend-Next.js-black)](https://nextjs.org/)
  [![WebSockets](https://img.shields.io/badge/Features-WebSockets-4e56a6)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
  
</div>

## 🚀 Overview

Onuze is a powerful, feature-rich community platform inspired by Reddit but enhanced with modern real-time capabilities. Our platform supports community creation, real-time discussions, moderation tools, and much more.

Visit us at [https://onuze.me](https://onuze.me)

<details>
<summary>📸 Screenshots</summary>
<br>
Coming soon
</details>

## ✨ Key Features

### 🏘️ Communities
- ✅ Create and customize your own communities
- ✅ Join and participate in existing communities
- ✅ Filter content by tags
- ✅ Advanced member management with ban/unban system
- ✅ Appeal system for banned members (permanent/temporary)

### 📝 Posts
- ✅ Create rich posts with text, images, and videos
- ✅ Pin important announcements (moderators only)
- ✅ Lock/unlock discussions
- ✅ Report inappropriate content
- ✅ Real-time comment updates via WebSockets

### 💬 Comments
- ✅ Participate in discussions with nested replies
- ✅ Edit and delete your own comments
- ✅ Report inappropriate comments
- ✅ Real-time notifications for new replies

### 🔔 Notifications
- ✅ Instant alerts for new comments and posts
- ✅ Moderation action notifications (ban/unban)

### 🔍 Search & Discovery
- ✅ Comprehensive search across posts, comments, and communities
- ✅ Advanced filtering options
- ✅ User profile views with content history

### 🛡️ Moderation Tools
- ✅ Community customization options
- ✅ Member appeal review system
- ✅ Comprehensive ban management

## 🏗️ Technology Stack

### Frontend
- **Framework**: Next.js
- **Real-time**: WebSockets
- **Styling**: Modern CSS with responsive design

### Backend
- **Framework**: Django
- **Real-time**: Django Channels
- **Database**: PostgreSQL
- **Media Storage**: BunnyNet CDN

## 📖 API Documentation

<details>
<summary>Community Endpoints</summary>

#### Collection Endpoints
- `GET /communities/` - List all communities
- `POST /communities/` - Create a new community
- `GET /communities/popular/` - Get top communities by member count

#### Detail Endpoints
- `GET /communities/{path}/` - Get community details
- `PUT /communities/{path}/` - Update a community (owner only)
- `PATCH /communities/{path}/` - Partially update a community
- `DELETE /communities/{path}/` - Delete a community (owner only)

[See all community endpoints](./COMMUNITIES_API.md)
</details>

<details>
<summary>Post Endpoints</summary>

#### Collection Endpoints
- `GET /posts/` - List all posts with filtering options
- `POST /posts/` - Create a new post
- `GET /posts/pinned/` - Get pinned posts

#### Detail Endpoints
- `GET /posts/{path}/` - Get a specific post
- `PUT /posts/{path}/` - Update a post (owner only)
- `PATCH /posts/{path}/` - Partially update a post
- `DELETE /posts/{path}/` - Delete a post (owner/moderator only)

[See all post endpoints](./POSTS_API.md)
</details>

<details>
<summary>Comment Endpoints</summary>

#### Collection Endpoints
- `GET /comments/` - List all comments with filtering options
- `POST /comments/` - Create a new comment

#### Detail Endpoints
- `GET /comments/{id}/` - Get a specific comment
- `PUT /comments/{id}/` - Update a comment (owner only)
- `PATCH /comments/{id}/` - Partially update a comment
- `DELETE /comments/{id}/` - Delete a comment (owner only)

[See all comment endpoints](./COMMENTS_API.md)
</details>

<details>
<summary>Other Endpoints</summary>

- **Search API** - [Details](./SEARCH_API.md)
- **Media Upload API** - For images and videos
- **Vote API** - [Details](./UPLOADS_API.md)
- **Notification API** - [Details](./NOTIFICATIONS_API.md)

</details>

## 🚀 Setup and Installation

### Backend Setup

<details>
<summary>Expand Instructions</summary>

1. Create a `.env` file in the backend folder with all required values:

```
# Django Settings
DEBUG=True
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
DATABASE_URL=postgres://user:password@localhost:5432/dbname

# Email Settings
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_password
DEFAULT_FROM_EMAIL=your_email@example.com

# Frontend URL
FRONTEND_URL=http://localhost:3000

# JWT Settings
JWT_SECRET_KEY=your_jwt_secret
JWT_ACCESS_TOKEN_LIFETIME=5
JWT_REFRESH_TOKEN_LIFETIME=1440

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Redis (for Channels)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

# Media Storage (BunnyNet)
USE_BUNNY_STORAGE=True
BUNNY_STORAGE_API_KEY=your_api_key
BUNNY_STORAGE_ZONE=your_zone
BUNNY_STORAGE_REGION=de
BUNNY_STORAGE_URL=your_storage_url
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Run the application:
```bash
daphne reddit_clone.asgi:application
```
</details>

### Frontend Setup

<details>
<summary>Expand Instructions</summary>

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Create a `.env.local` file:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. Install dependencies:
```bash
npm install
```

4. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`
</details>

## 📜 License

**CC BY-NC 4.0 with additional attribution requirement**

This project is licensed under Creative Commons Attribution-NonCommercial 4.0 International with additional requirements:

1. You must give **clear attribution** to the original author.
2. If used on a **public-facing website**, a visible credit such as "Powered by Onuze" with a link to this repository must be displayed.
3. Commercial use, redistribution for profit, or use in paid services is **strictly prohibited** without a separate commercial license agreement.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🙏 Acknowledgements

- Built with ❤️ by [shaongitbd](https://github.com/shaongitbd)
- For support or inquiries: shaongit@gmail.com

---

<div align="center">
  <sub>Remember to ⭐ this repository if you found it useful!</sub>
</div>
