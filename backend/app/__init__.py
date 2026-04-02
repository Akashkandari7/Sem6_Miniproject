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
        is_testing = app.config.get('TESTING', False)
        if db_uri.startswith('sqlite://') and not is_testing:
            db.create_all()

            # Seed if DB is empty (local dev or Vercel /tmp/ cold start)
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
    """Seed subjects, RBAC data, and a default admin user for fresh DB."""
    from app.models.subject import Subject
    from app.models.user import User
    from app.models.permission import Permission
    from app.models.role import Role

    # ── Permissions ────────────────────────────────────────────────
    _PERMISSIONS = [
        ('questions.create',      'questions', 'create',       'Add questions to the bank'),
        ('questions.read',        'questions', 'read',         'View questions'),
        ('questions.update',      'questions', 'update',       'Edit existing questions'),
        ('questions.delete',      'questions', 'delete',       'Remove questions from the bank'),
        ('questions.generate_ai', 'questions', 'generate_ai',  'Generate questions via AI'),
        ('papers.create',         'papers',    'create',       'Generate exam papers'),
        ('papers.read',           'papers',    'read',         'View exam papers'),
        ('papers.update',         'papers',    'update',       'Edit paper questions'),
        ('papers.delete',         'papers',    'delete',       'Delete exam papers'),
        ('papers.download_pdf',   'papers',    'download_pdf', 'Download paper as PDF'),
        ('subjects.create',       'subjects',  'create',       'Create subjects'),
        ('subjects.read',         'subjects',  'read',         'View subjects'),
        ('subjects.update',       'subjects',  'update',       'Edit subjects'),
        ('subjects.delete',       'subjects',  'delete',       'Delete subjects'),
        ('users.read_self',       'users',     'read_self',    'View own profile'),
        ('users.list',            'users',     'list',         'List all users'),
        ('users.create',          'users',     'create',       'Create user accounts'),
        ('users.update',          'users',     'update',       'Edit user accounts'),
        ('users.delete',          'users',     'delete',       'Delete user accounts'),
    ]

    perm_map = {}
    for name, resource, action, desc in _PERMISSIONS:
        p = Permission(name=name, resource=resource, action=action, description=desc)
        db.session.add(p)
        perm_map[name] = p

    # ── Roles ──────────────────────────────────────────────────────
    def _perms(*names):
        return [perm_map[n] for n in names]

    admin_role = Role(
        name='admin',
        description='Full access to all resources',
        permissions=list(perm_map.values()),
    )

    teacher_role = Role(
        name='teacher',
        description='Manage questions, papers, and view subjects',
        permissions=_perms(
            'questions.create', 'questions.read', 'questions.update',
            'questions.delete', 'questions.generate_ai',
            'papers.create', 'papers.read', 'papers.update',
            'papers.delete', 'papers.download_pdf',
            'subjects.read',
            'users.read_self',
        ),
    )

    viewer_role = Role(
        name='viewer',
        description='Read-only access to questions, papers, and subjects',
        permissions=_perms(
            'questions.read',
            'papers.read', 'papers.download_pdf',
            'subjects.read',
            'users.read_self',
        ),
    )

    db.session.add_all([admin_role, teacher_role, viewer_role])

    # ── Default subject ────────────────────────────────────────────
    cs = Subject(name='Computer Science', code='CS101', description='Core CS subject')
    db.session.add(cs)

    # ── Default admin user ─────────────────────────────────────────
    admin_user = User(username='admin', email='admin@qpgen.com')
    admin_user.set_password('admin123')
    admin_user.roles = [admin_role]
    db.session.add(admin_user)

    db.session.commit()