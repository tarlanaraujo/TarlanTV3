# IPTV Manager

## Overview

IPTV Manager is a Flask-based web application that allows users to search, validate, and manage IPTV playlist URLs. The application can process M3U/M3U8 files directly or scrape websites to find IPTV links, validate channel connectivity, and export working playlists.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
The application uses Flask as the web framework with SQLAlchemy for database operations. The architecture follows a modular approach with separated concerns:

- **Flask Application**: Main application setup in `app.py` with configuration and database initialization
- **Database Models**: SQLAlchemy models in `models.py` for data persistence
- **Route Handlers**: Web routes and API endpoints in `routes.py`
- **Business Logic**: Separate modules for M3U validation (`m3u_validator.py`) and web scraping (`web_scraper.py`)

### Frontend Architecture
The frontend uses Bootstrap 5 with a dark theme for responsive design:

- **Templates**: Jinja2 templates in the `templates/` directory with base template inheritance
- **Static Assets**: CSS and JavaScript files in the `static/` directory
- **Client-side Features**: JavaScript for form validation, auto-refresh, and interactive elements

### Data Storage
Uses SQLAlchemy ORM with PostgreSQL database:

- **Database**: PostgreSQL database with automatic table creation
- **Connection**: Configured via `DATABASE_URL` environment variable
- **Connection Management**: Pool recycling and pre-ping for connection reliability
- **Tables**: search_history, channel, playlist_export with proper foreign key relationships

## Key Components

### Database Models
- **SearchHistory**: Tracks playlist search requests and their processing status
- **Channel**: Stores individual channel information with validation status
- **PlaylistExport**: Manages exported playlist files and metadata

### Core Services
- **M3UValidator**: Handles M3U/M3U8 file parsing, validation, and channel extraction
- **WebScraper**: Uses Trafilatura for content extraction and M3U link discovery
- **Background Processing**: Threading for non-blocking playlist processing

### Web Interface
- **Search Interface**: URL input form with validation
- **Validation Display**: Real-time status updates and channel listing
- **Export Functionality**: M3U playlist generation and download

## Data Flow

1. **Search Initiation**: User submits URL through web interface
2. **Background Processing**: System determines if URL is direct M3U or webpage
3. **Content Extraction**: Either downloads M3U directly or scrapes webpage for links
4. **Channel Parsing**: Extracts channel information from M3U content
5. **Validation**: Tests channel connectivity (optional/background process)
6. **Display**: Shows results with categorized channel listing
7. **Export**: Generates downloadable M3U files with working channels

## External Dependencies

### Python Packages
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and management
- **Requests**: HTTP client for URL fetching
- **Trafilatura**: Web content extraction
- **Werkzeug**: WSGI utilities and middleware

### Frontend Libraries
- **Bootstrap 5**: UI framework with dark theme
- **Font Awesome**: Icon library
- **JavaScript**: Client-side interactivity and validation

### External Services
- **Web Scraping**: Accesses external websites to find M3U links
- **M3U Validation**: Tests connectivity to streaming URLs
- **User-Agent Spoofing**: Mimics browser requests to avoid blocking

## Deployment Strategy

### Development
- **Local Development**: Flask development server on port 5000
- **Debug Mode**: Enabled for development with detailed error reporting
- **SQLite Database**: Local file-based database for development

### Production Considerations
- **Environment Variables**: Configuration via environment variables
- **Database**: Support for PostgreSQL or other production databases
- **Proxy Handling**: ProxyFix middleware for reverse proxy deployments
- **Session Management**: Configurable secret key for session security
- **Logging**: Configurable logging levels for monitoring

### Security Features
- **Input Validation**: URL validation and sanitization
- **Session Security**: Secure session management
- **Request Timeouts**: Prevents hanging requests
- **Error Handling**: Graceful error handling and user feedback

The application is designed to be easily deployable on platforms like Replit, with environment-based configuration and support for both development and production environments.