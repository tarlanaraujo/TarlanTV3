# IPTV Manager

## Overview

IPTV Manager is a Flask-based web application that allows users to upload, parse, and manage M3U/M3U8 playlist files. The application provides a professional interface for viewing IPTV channels, movies, and series with automatic categorization, search functionality, and channel validation capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
The application uses Flask as the web framework with SQLAlchemy for database operations. The architecture follows a modular approach with separated concerns:

- **Flask Application**: Main application setup in `app.py` with configuration, database initialization, and middleware setup
- **Database Models**: SQLAlchemy models in `models.py` for data persistence using declarative base
- **Route Handlers**: Web routes and API endpoints in `routes.py` for handling user requests
- **Business Logic**: Separate modules for M3U validation (`m3u_validator.py`) and web scraping (`web_scraper.py`)

### Frontend Architecture
The frontend uses Bootstrap 5 with a dark theme for responsive design:

- **Templates**: Jinja2 templates with base template inheritance for consistent layout
- **Static Assets**: CSS and JavaScript files for styling and client-side functionality
- **Responsive Design**: Mobile-first approach with Bootstrap grid system
- **Interactive Elements**: JavaScript for form validation, auto-refresh, and player controls

### Data Storage
Uses SQLAlchemy ORM with configurable database backend:

- **Database**: Configurable via `DATABASE_URL` environment variable (defaults to SQLite)
- **Connection Management**: Pool recycling and pre-ping for connection reliability
- **Schema**: Automatic table creation on application startup

## Key Components

### Database Models
- **M3UPlaylist**: Stores playlist metadata including name, source URL, channel counts, and processing status
- **Channel**: Individual channel information with categorization, validation status, and metadata
- **SearchHistory**: Tracks search queries and results for user convenience

### Core Services
- **M3UValidator**: Handles M3U/M3U8 file parsing, channel extraction, and URL validation
- **WebScraper**: Extracts M3U content from web pages and handles content detection
- **Background Processing**: Threading for non-blocking playlist processing and channel validation

### Web Interface
- **Upload Interface**: Support for both URL and file upload methods
- **Category Views**: Separate views for live channels, movies, and series
- **Search Functionality**: Real-time search across all channels with filtering
- **Player Integration**: Built-in video player with HLS support

## Data Flow

1. **Upload Process**: User uploads M3U file or provides URL → Content validation → Background parsing
2. **Parsing Flow**: Extract channel information → Categorize content → Validate URLs → Store in database
3. **Display Flow**: Retrieve channels from database → Apply filters/search → Render in appropriate view
4. **Player Flow**: Select channel → Load player with stream URL → Handle playback controls

## External Dependencies

### Backend Dependencies
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and schema management
- **Requests**: HTTP client for URL validation and content fetching
- **Werkzeug**: WSGI utilities and proxy fix middleware

### Frontend Dependencies
- **Bootstrap 5**: UI framework and responsive design
- **Font Awesome**: Icon library for UI elements
- **Custom JavaScript**: Player controls and interactive features

### Optional Integrations
- **PostgreSQL**: Production database backend (via DATABASE_URL)
- **ProxyFix**: Reverse proxy support for deployment

## Deployment Strategy

### Environment Configuration
- **SESSION_SECRET**: Flask session encryption key
- **DATABASE_URL**: Database connection string (defaults to SQLite)
- **Debug Mode**: Configurable for development vs production

### Database Setup
- **Auto-initialization**: Tables created automatically on first run
- **Migration Support**: Schema changes handled through SQLAlchemy
- **Connection Pooling**: Built-in connection management for reliability

### Production Considerations
- **WSGI Deployment**: Compatible with Gunicorn, uWSGI, or similar servers
- **Proxy Support**: ProxyFix middleware for reverse proxy setups
- **Static Files**: Served through Flask in development, external server in production
- **Logging**: Configurable logging levels for monitoring and debugging

### Security Features
- **Input Validation**: URL and file validation before processing
- **Content Sanitization**: Safe handling of user-provided M3U content
- **Session Management**: Secure session handling with configurable secrets
- **CSRF Protection**: Built-in Flask security features