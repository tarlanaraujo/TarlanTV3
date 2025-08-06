import os
from app import app

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Disable debug mode in production
    debug_mode = not (os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RAILWAY_ENVIRONMENT'))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
