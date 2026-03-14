import os
from flask import Flask, send_from_directory
from app.config import config
from app.extensions import db, migrate, jwt, cors, ma


def create_app(config_name='default'):
    """
    App Factory Pattern - creates and configures the Flask app.
    Calling create_app('testing') gives a test app, 
    create_app('production') gives prod app. Same code, different behavior.
    """
    # Point Flask at the frontend folder for static HTML serving
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'))
    app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
    
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

    # Serve frontend HTML pages
    @app.route('/')
    @app.route('/index')
    def serve_index():
        return send_from_directory(frontend_dir, 'index.html')

    @app.route('/dashboard')
    def serve_dashboard():
        return send_from_directory(frontend_dir, 'dashboard.html')

    @app.route('/questions')
    def serve_questions():
        return send_from_directory(frontend_dir, 'questions.html')

    @app.route('/generate')
    def serve_generate():
        return send_from_directory(frontend_dir, 'generate.html')

    return app 