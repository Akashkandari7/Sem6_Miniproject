import sys
import os

# Add backend directory to Python path so 'from app import ...' works
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import create_app

config_name = os.getenv('FLASK_ENV', 'production')
app = create_app(config_name)
