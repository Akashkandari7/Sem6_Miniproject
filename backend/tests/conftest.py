import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.subject import Subject

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
    """Seed the database with a user and a subject for tests."""
    with app.app_context():
        user = User(username='testuser', email='test@test.com', role='teacher')
        user.set_password('password123')
        db.session.add(user)
        
        subject = Subject(name='Unit Test Subject', code='UT100', description='For testing')
        db.session.add(subject)
        db.session.commit()
        
        yield {
            'user_id': user.id,
            'subject_id': subject.id
        }

@pytest.fixture
def auth_headers(client, init_database):
    """Returns authorization headers for the test user."""
    res = client.post('/api/auth/login', json={
        'email': 'test@test.com',
        'password': 'password123'
    })
    token = res.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}
