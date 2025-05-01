<div align="center">
  <img src="https://onuze.me/logo.png" alt="Onuze" width="180">
  
  # Onuze

  <p>A modern, real-time community platform built for engagement</p>

  [![Website](https://img.shields.io/badge/Website-onuze.me-FF424D)](https://onuze.me)
  [![License](https://img.shields.io/badge/License-CC_BY_NC_4.0-lightgrey)](#license)
  [![Django](https://img.shields.io/badge/Backend-Django-092E20)](https://www.djangoproject.com/)
  [![Next.js](https://img.shields.io/badge/Frontend-Next.js-black)](https://nextjs.org/)
  [![WebSockets](https://img.shields.io/badge/Features-WebSockets-4e56a6)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
  [![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791)](https://www.postgresql.org/)
  
  <br/>
  
  <a href="https://onuze.me">
    <img src="https://img.shields.io/badge/View_Demo-Visit_Website-FF424D?style=for-the-badge" alt="View Demo" />
  </a>
  
</div>

<br/>

<p align="center">
  <b>Onuze</b> is a modern Reddit-inspired platform with real-time capabilities, comprehensive moderation tools, and a beautiful UI designed for maximum engagement.
</p>

<details open>
<summary>📋 Table of Contents</summary>

- [✨ Features](#-key-features)
- [🏗️ Technology Stack](#️-technology-stack)
- [🖥️ Demo](#️-demo)
- [🚀 Getting Started](#-getting-started)
- [📖 API Documentation](#-api-documentation)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)
- [👥 Team](#-team)

</details>

## 🖥️ Demo

<div align="center">
  <a href="https://onuze.me">
    <img src="https://via.placeholder.com/800x400?text=Onuze+Platform+Screenshot" alt="Onuze Demo" width="80%" />
  </a>
  <p><i>Live demo available at <a href="https://onuze.me">onuze.me</a></i></p>
</div>

## ✨ Key Features

<table>
  <tr>
    <td width="50%">
      <h3 align="center">🏘️ Communities</h3>
      <ul>
        <li>✅ Create and customize your own communities</li>
        <li>✅ Join and participate in existing communities</li>
        <li>✅ Filter content by tags</li>
        <li>✅ Advanced member management with ban/unban system</li>
        <li>✅ Appeal system for banned members</li>
      </ul>
    </td>
    <td width="50%">
      <h3 align="center">📝 Posts</h3>
      <ul>
        <li>✅ Create rich posts with text, images, and videos</li>
        <li>✅ Pin important announcements (moderators only)</li>
        <li>✅ Lock/unlock discussions</li>
        <li>✅ Report inappropriate content</li>
        <li>✅ Real-time comment updates via WebSockets</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3 align="center">💬 Comments</h3>
      <ul>
        <li>✅ Participate in discussions with nested replies</li>
        <li>✅ Edit and delete your own comments</li>
        <li>✅ Report inappropriate comments</li>
        <li>✅ Real-time notifications for new replies</li>
      </ul>
    </td>
    <td width="50%">
      <h3 align="center">🛡️ Moderation Tools</h3>
      <ul>
        <li>✅ Community customization options</li>
        <li>✅ Member appeal review system</li>
        <li>✅ Comprehensive ban management</li>
        <li>✅ Post and comment moderation</li>
      </ul>
    </td>
  </tr>
</table>

<details>
<summary>View More Features</summary>

### 🔔 Notifications
- ✅ Instant alerts for new comments and posts
- ✅ Moderation action notifications (ban/unban)
- ✅ Customizable notification preferences

### 🔍 Search & Discovery
- ✅ Comprehensive search across posts, comments, and communities
- ✅ Advanced filtering options
- ✅ User profile views with content history

</details>

## 🏗️ Technology Stack

<table>
  <tr>
    <td align="center" width="20%">
      <img src="https://cdn.worldvectorlogo.com/logos/nextjs-2.svg" width="50" height="50"/><br/>
      <strong>Next.js</strong><br/>
      Frontend Framework
    </td>
    <td align="center" width="20%">
      <img src="https://cdn.worldvectorlogo.com/logos/django.svg" width="50" height="50"/><br/>
      <strong>Django</strong><br/>
      Backend Framework
    </td>
    <td align="center" width="20%">
      <img src="https://cdn.worldvectorlogo.com/logos/postgresql.svg" width="50" height="50"/><br/>
      <strong>PostgreSQL</strong><br/>
      Database
    </td>
    <td align="center" width="20%">
      <img src="https://cdn.worldvectorlogo.com/logos/redis.svg" width="50" height="50"/><br/>
      <strong>Redis</strong><br/>
      WebSocket & Caching
    </td>
    <td align="center" width="20%">
      <img src="https://static.wikia.nocookie.net/logopedia/images/7/73/BunnyNET_logo.svg" width="50" height="50"/><br/>
      <strong>BunnyNet</strong><br/>
      Media Storage
    </td>
  </tr>
</table>

## 🚀 Getting Started

### System Requirements

- Python 3.8+
- Node.js 14+
- PostgreSQL 12+
- Redis 6+

### Backend Setup

<details>
<summary>Expand Instructions</summary>

1. Clone the repository
```bash
git clone https://github.com/shaongitbd/onuze.git
cd onuze
```

2. Create a `.env` file in the backend folder with all required values:

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

3. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser (admin):
```bash
python manage.py createsuperuser
```

6. Run the application:
```bash
daphne reddit_clone.asgi:application
```

The backend API will be available at `http://localhost:8000`
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

5. For production build:
```bash
npm run build
npm start
```
</details>

## 📖 API Documentation

We provide a comprehensive API that powers our platform's functionality. Detailed documentation for each endpoint is available in separate markdown files.

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

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Contributing Guidelines

1. **Fork the repository**
2. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Run tests**
5. **Submit a pull request**

### Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## 📈 Project Stats

<div align="center">
  <img src="https://img.shields.io/github/stars/shaongitbd/onuze?style=social" alt="GitHub stars" />
  <img src="https://img.shields.io/github/forks/shaongitbd/onuze?style=social" alt="GitHub forks" />
  <img src="https://img.shields.io/github/issues/shaongitbd/onuze" alt="GitHub issues" />
  <img src="https://img.shields.io/github/last-commit/shaongitbd/onuze" alt="Last commit" />
</div>

## 📜 License

**CC BY-NC 4.0 with additional attribution requirement**

This project is licensed under Creative Commons Attribution-NonCommercial 4.0 International with additional requirements:

1. You must give **clear attribution** to the original author.
2. If used on a **public-facing website**, a visible credit such as "Powered by Onuze" with a link to this repository must be displayed.
3. Commercial use, redistribution for profit, or use in paid services is **strictly prohibited** without a separate commercial license agreement.

## 👥 Team

<div align="center">
  <a href="https://github.com/shaongitbd">
    <img src="https://github.com/shaongitbd.png" width="100" height="100" style="border-radius:50%"/>
    <br/>
    <b>Shao</b>
    <br/>
    <i>Lead Developer</i>
  </a>
</div>

<br/>

## 📞 Support

Need help? Feel free to reach out:

- 📧 Email: [shaongit@gmail.com](mailto:shaongit@gmail.com)
- 🌐 Website: [onuze.me](https://onuze.me)

---

<div align="center">
  <sub>If you found this project helpful, please consider giving it a ⭐️!</sub>
  <br/>
  <br/>
  <a href="https://onuze.me">
    <img src="https://img.shields.io/badge/Built_with_❤️_by-Shao-FF424D?style=for-the-badge" alt="Built with love" />
  </a>
</div>
