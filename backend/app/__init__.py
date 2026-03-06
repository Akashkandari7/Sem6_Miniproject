import os
from flask import Flask, send_from_directory
from app.config import config
from app.extensions import db, migrate, jwt, cors, ma

# Path to frontend directory (one level up from backend)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'frontend')


def create_app(config_name='default'):
    """
    App Factory Pattern - creates and configures the Flask app.
    Calling create_app('testing') gives a test app, 
    create_app('production') gives prod app. Same code, different behavior.
    """
    app = Flask(__name__)
    
    # Load config
    app.config.from_object(config[config_name])
    
    # Initialize extensions WITH the app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)
    ma.init_app(app)
    
    # Register blueprints (routes)
    from app.routes.auth import auth_bp
    from app.routes.questions import questions_bp
    from app.routes.papers import papers_bp
    from app.routes.subjects import subjects_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(questions_bp, url_prefix='/api/questions')
    app.register_blueprint(papers_bp, url_prefix='/api/papers')
    app.register_blueprint(subjects_bp, url_prefix='/api/subjects')
    
    # Health check route
    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'message': 'Server is running'}
    
    # Serve frontend HTML files
    @app.route('/')
    def serve_index():
        return send_from_directory(FRONTEND_DIR, 'index.html')
    
    @app.route('/<path:filename>')
    def serve_frontend(filename):
        return send_from_directory(FRONTEND_DIR, filename)
    
    return app 