import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.subject import Subject
from app.models.permission import Permission
from app.models.role import Role


@pytest.fixture
def app():
    """Create and configure a new app instance for testing."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def init_database(app):
    """
    Seed a minimal but complete dataset for auth and generator tests.

    Creates the full permission + role set so that RBAC-protected routes work
    in tests.  The test user is assigned the 'teacher' role.
    """
    with app.app_context():
        # ── Permissions ───────────────────────────────────────────
        _PERMS = [
            ('questions.create',      'questions', 'create',       'Add questions'),
            ('questions.read',        'questions', 'read',         'View questions'),
            ('questions.update',      'questions', 'update',       'Edit questions'),
            ('questions.delete',      'questions', 'delete',       'Delete questions'),
            ('questions.generate_ai', 'questions', 'generate_ai',  'AI generation'),
            ('papers.create',         'papers',    'create',       'Generate papers'),
            ('papers.read',           'papers',    'read',         'View papers'),
            ('papers.update',         'papers',    'update',       'Edit papers'),
            ('papers.delete',         'papers',    'delete',       'Delete papers'),
            ('papers.download_pdf',   'papers',    'download_pdf', 'Download PDF'),
            ('subjects.create',       'subjects',  'create',       'Create subjects'),
            ('subjects.read',         'subjects',  'read',         'View subjects'),
            ('subjects.update',       'subjects',  'update',       'Edit subjects'),
            ('subjects.delete',       'subjects',  'delete',       'Delete subjects'),
            ('users.read_self',       'users',     'read_self',    'View own profile'),
            ('users.list',            'users',     'list',         'List users'),
            ('users.create',          'users',     'create',       'Create users'),
            ('users.update',          'users',     'update',       'Edit users'),
            ('users.delete',          'users',     'delete',       'Delete users'),
        ]
        perm_map = {}
        for name, resource, action, desc in _PERMS:
            p = Permission(name=name, resource=resource, action=action, description=desc)
            db.session.add(p)
            perm_map[name] = p

        # ── Roles ─────────────────────────────────────────────────
        admin_role = Role(name='admin', description='Full access')
        admin_role.permissions = list(perm_map.values())

        teacher_role = Role(name='teacher', description='Manage questions and papers')
        teacher_role.permissions = [
            perm_map[n] for n in (
                'questions.create', 'questions.read', 'questions.update',
                'questions.delete', 'questions.generate_ai',
                'papers.create', 'papers.read', 'papers.update',
                'papers.delete', 'papers.download_pdf',
                'subjects.read',
                'users.read_self',
            )
        ]

        viewer_role = Role(name='viewer', description='Read-only access')
        viewer_role.permissions = [
            perm_map[n] for n in (
                'questions.read', 'papers.read', 'papers.download_pdf',
                'subjects.read', 'users.read_self',
            )
        ]
        db.session.add_all([admin_role, teacher_role, viewer_role])

        # ── Test user (teacher role) ───────────────────────────────
        user = User(username='testuser', email='test@test.com')
        user.set_password('password123')
        user.roles = [teacher_role]
        db.session.add(user)

        subject = Subject(name='Unit Test Subject', code='UT100', description='For testing')
        db.session.add(subject)
        db.session.commit()

        yield {
            'user_id': user.id,
            'subject_id': subject.id,
        }


@pytest.fixture
def auth_headers(client, init_database):
    """Return Authorization headers for the seeded test user."""
    res = client.post('/api/auth/login', json={
        'email': 'test@test.com',
        'password': 'password123',
    })
    token = res.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}
