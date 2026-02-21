# This file is kept for compatibility only.
# The actual app is created in app/__init__.py
# Use run.py to start the server

from app import create_app
from app.extensions import db

app = create_app('development') 