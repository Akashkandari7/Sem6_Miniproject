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
    
    # Auto-create tables and seed data ONLY for local/ephemeral SQLite databases.
    # Running db.create_all() against a remote PostgreSQL DB on Vercel cold starts
    # causes severe latency, function timeouts, and potential race conditions.
    with app.app_context():
        from app.models.question import Question
        from app.models.user import User
        from app.models.subject import Subject
        
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if db_uri.startswith('sqlite://'):
            db.create_all()
            
            # Seed if DB is empty (local or cold start on Vercel /tmp/ db)
            if Subject.query.first() is None:
                _seed_initial_data(db)

    # Secure setup endpoint for initializing persistent production databases (Postgres, etc)
    @app.route('/api/setup', methods=['GET', 'POST'])
    def setup_db():
        from flask import request, jsonify
        from app.models.subject import Subject
        
        # Require SECRET_KEY as a security measure
        secret = request.args.get('key')
        if not secret or secret != app.config.get('SECRET_KEY'):
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid key. Pass ?key=<your_secret_key>'}), 401
            
        try:
            db.create_all()
            if Subject.query.first() is None:
                _seed_initial_data(db)
                return jsonify({'status': 'ok', 'message': 'Database tables created and seeded successfully.'})
            return jsonify({'status': 'ok', 'message': 'Database tables created. Existing data found.'})
        except Exception as e:
            return jsonify({'error': 'Setup failed', 'details': str(e)}), 500
    
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


def _seed_initial_data(db):
    """Seed subjects and a default admin user for fresh DB."""
    from app.models.subject import Subject
    from app.models.user import User
    
    # Add default subject
    cs = Subject(name='Computer Science', code='CS101', description='Core CS subject')
    db.session.add(cs)
    
    # Add default admin user
    admin = User(username='admin', email='admin@qpgen.com')
    admin.set_password('admin123')
    db.session.add(admin)
    
    db.session.commit()