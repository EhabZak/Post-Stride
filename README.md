# Post_Stride Backend

A Flask-based backend for a social media management application that allows users to schedule and publish posts across multiple social media platforms.

## Features

- **User Management**: User registration, authentication, and profile management
- **Social Platform Integration**: Support for LinkedIn, Instagram, X (Twitter), TikTok, and Facebook
- **Post Management**: Create, schedule, and manage posts across multiple platforms
- **Media Management**: Upload and organize media files (images, videos, GIFs, audio, documents)
- **Cross-Platform Publishing**: Schedule posts to be published on multiple social platforms simultaneously
- **Status Tracking**: Monitor post status across different platforms

## Database Schema

### Core Tables

1. **users** - User accounts and authentication
2. **social_platforms** - Available social media platforms
3. **user_platforms** - User connections to social platforms (OAuth tokens)
4. **posts** - Post content and scheduling information
5. **post_platforms** - Platform-specific post data and publishing status
6. **media** - User-uploaded media files
7. **post_media** - Many-to-many relationship between posts and media

### Key Relationships

- Users can connect to multiple social platforms
- Posts can be scheduled for multiple platforms
- Media can be attached to multiple posts
- All relationships maintain referential integrity with cascade deletes

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
FLASK_APP=app
FLASK_ENV=development
DATABASE_URL=postgresql://username:password@localhost:5432/post_stride_db
SECRET_KEY=your-secret-key-here
```

### 3. Database Setup

Run the migration script to create all tables:

```bash
python migrations/create_tables.py
```

### 4. Run the Application

```bash
flask run
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

### Users
- `GET /api/users/me` - Get current user profile
- `PUT /api/users/me` - Update user profile

### Social Platforms
- `GET /api/platforms` - List available social platforms
- `POST /api/platforms/connect` - Connect user to a platform
- `GET /api/platforms/connected` - Get user's connected platforms

### Posts
- `GET /api/posts` - List user's posts
- `POST /api/posts` - Create a new post
- `GET /api/posts/<id>` - Get post details
- `PUT /api/posts/<id>` - Update post
- `DELETE /api/posts/<id>` - Delete post

### Media
- `GET /api/media` - List user's media files
- `POST /api/media` - Upload new media
- `DELETE /api/media/<id>` - Delete media file

## Database Indexes

The application includes optimized database indexes for:

- User platform connections (unique constraint)
- Post scheduling and status queries
- Media organization by user and creation date
- Platform-specific post tracking

## Security Features

- Password hashing with Werkzeug
- UUID-based primary keys for enhanced security
- OAuth token management for social platform connections
- User session management with Flask-Login

## Development

### Adding New Social Platforms

1. Add the platform to the `social_platforms` table
2. Implement platform-specific API integration
3. Update the `PostPlatform` model if needed

### Database Migrations

Use Flask-Migrate for database schema changes:

```bash
flask db init
flask db migrate -m "Description of changes"
flask db upgrade
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
