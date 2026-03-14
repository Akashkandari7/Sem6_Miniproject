# This file is kept for compatibility only.
# The actual app is created in app/__init__.py
# Use run.py to start the server

import os
from app import create_app
from app.extensions import db

config_name = os.getenv('FLASK_ENV', 'production')
app = create_app(config_name)