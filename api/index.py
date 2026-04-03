import os
import sys

# Add the backend directory to the sys.path so we can import the app
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app import create_app

# Set config based on environment variable (default to production on Vercel)
config_name = os.getenv('APP_CONFIG', 'production')
app = create_app(config_name)
