# Reddit Clone

A modern, secure, and scalable social platform inspired by Reddit, built with Django, Django Rest Framework, Django Channels, and React.

## Backend Features

- **User Management**: Registration, authentication, profiles, and karma system
- **Communities**: Create and join topic-based communities
- **Content**: Posts, nested comments, and media uploads
- **Voting System**: Upvote/downvote posts and comments
- **Real-time Features**: Live updates for new posts, comments, and notifications
- **Moderation Tools**: Report content, ban users, and manage communities
- **Security**: JWT authentication, rate limiting, and input validation

## Tech Stack

- **Backend**:
  - Django & Django REST Framework
  - Django Channels for WebSockets/real-time features
  - PostgreSQL database
  - Redis for caching and Channels layer
  - JWT authentication

- **Frontend**:
  - React (to be implemented)
  - Redux/Zustand for state management
  - Socket.io/WebSockets for real-time updates

## Setup Instructions

### Prerequisites

- Python 3.9+
- PostgreSQL
- Redis (for production)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/reddit-clone.git
   cd reddit-clone
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Create a `.env` file in the project root
   - Add required environment variables (see `.env.example`)

5. Run database migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Start the development server:
   ```bash
   python manage.py runserver
   ```

8. For WebSocket support, run Daphne:
   ```bash
   daphne -p 8001 reddit_clone.asgi:application
   ```

### Running with Docker (Production)

1. Build the Docker image:
   ```bash
   docker-compose build
   ```

2. Start the containers:
   ```bash
   docker-compose up
   ```

## API Documentation

Once the server is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## Testing

Run the tests with pytest:

```bash
pytest
```

For test coverage:

```bash
coverage run -m pytest
coverage report
```

## Security Features

- JWT authentication with refresh tokens
- Password hashing with Argon2
- CSRF protection and secure cookies
- Rate limiting and brute force protection
- Input validation and sanitization
- WebSocket authentication
- Audit logging for sensitive operations

## Project Structure

```
reddit_clone/
├── communities/       # Community management
├── posts/             # Post creation and management
├── comments/          # Comment functionality
├── votes/             # Voting system
├── users/             # User management
├── notifications/     # Notification system
├── moderation/        # Content moderation
├── messaging/         # Private messaging
├── security/          # Security-related features
└── reddit_clone/      # Project settings
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 