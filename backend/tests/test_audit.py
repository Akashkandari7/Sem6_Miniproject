"""
Tests for the audit logging system.

Verifies that audit log entries are created for auth events,
write operations (CRUD), AI generation, and permission denials.
"""

from app.extensions import db
from app.models.audit_log import AuditLog


# ── Helpers ────────────────────────────────────────────────────────────────────

def _last_log(app, action):
    with app.app_context():
        return (
            AuditLog.query
            .filter_by(action=action)
            .order_by(AuditLog.id.desc())
            .first()
        )


# ── Auth events ────────────────────────────────────────────────────────────────

def test_login_success_creates_audit_log(client, init_database, app):
    client.post('/api/auth/login', json={'email': 'test@test.com', 'password': 'password123'})
    log = _last_log(app, 'auth.login')
    assert log is not None
    assert log.status == 'success'
    assert log.user_id == init_database['user_id']


def test_login_failure_creates_audit_log(client, init_database, app):
    client.post('/api/auth/login', json={'email': 'test@test.com', 'password': 'wrongpass'})
    log = _last_log(app, 'auth.login')
    assert log is not None
    assert log.status == 'failure'
    assert log.details['email'] == 'test@test.com'


def test_register_creates_audit_log(client, init_database, app):
    client.post('/api/auth/register', json={
        'username': 'newuser',
        'email': 'new@test.com',
        'password': 'pass1234',
    })
    log = _last_log(app, 'auth.register')
    assert log is not None
    assert log.status == 'success'
    assert log.resource_type == 'user'
    assert log.details['username'] == 'newuser'


# ── Permission denied ──────────────────────────────────────────────────────────

def test_permission_denied_creates_audit_log(client, init_database, app):
    # Viewer lacks subjects.create — use a fresh viewer user
    from app.models.user import User
    from app.models.role import Role

    with app.app_context():
        viewer_role = Role.query.filter_by(name='viewer').first()
        viewer = User(username='viewer1', email='viewer@test.com')
        viewer.set_password('pass1234')
        viewer.roles = [viewer_role]
        db.session.add(viewer)
        db.session.commit()

    res = client.post('/api/auth/login', json={'email': 'viewer@test.com', 'password': 'pass1234'})
    token = res.get_json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    client.post('/api/subjects/', json={'name': 'X', 'code': 'X100'}, headers=headers)

    log = _last_log(app, 'auth.permission_denied')
    assert log is not None
    assert log.status == 'failure'
    assert 'subjects.create' in log.details.get('required_permission', '')


# ── Question CRUD ──────────────────────────────────────────────────────────────

def test_create_question_creates_audit_log(client, init_database, app):
    res = client.post('/api/auth/login', json={'email': 'test@test.com', 'password': 'password123'})
    headers = {'Authorization': f'Bearer {res.get_json()["access_token"]}'}

    client.post('/api/questions/', json={
        'text': 'What is 2+2?',
        'question_type': 'mcq',
        'blooms_level': 'remember',
        'difficulty': 'easy',
        'marks': 1,
        'subject_id': init_database['subject_id'],
        'option_a': '3', 'option_b': '4', 'option_c': '5', 'option_d': '6',
        'correct_answer': 'b',
    }, headers=headers)

    log = _last_log(app, 'question.create')
    assert log is not None
    assert log.status == 'success'
    assert log.resource_type == 'question'
    assert log.resource_id is not None
    assert log.details['question_type'] == 'mcq'


def test_update_question_creates_audit_log(client, init_database, app):
    res = client.post('/api/auth/login', json={'email': 'test@test.com', 'password': 'password123'})
    headers = {'Authorization': f'Bearer {res.get_json()["access_token"]}'}

    created = client.post('/api/questions/', json={
        'text': 'Original text',
        'question_type': 'short',
        'blooms_level': 'understand',
        'difficulty': 'medium',
        'marks': 2,
        'subject_id': init_database['subject_id'],
    }, headers=headers)
    qid = created.get_json()['question']['id']

    client.put(f'/api/questions/{qid}', json={'text': 'Updated text'}, headers=headers)

    log = _last_log(app, 'question.update')
    assert log is not None
    assert log.resource_id == qid


def test_delete_question_creates_audit_log(client, init_database, app):
    res = client.post('/api/auth/login', json={'email': 'test@test.com', 'password': 'password123'})
    headers = {'Authorization': f'Bearer {res.get_json()["access_token"]}'}

    created = client.post('/api/questions/', json={
        'text': 'To be deleted',
        'question_type': 'short',
        'blooms_level': 'apply',
        'difficulty': 'hard',
        'marks': 3,
        'subject_id': init_database['subject_id'],
    }, headers=headers)
    qid = created.get_json()['question']['id']

    client.delete(f'/api/questions/{qid}', headers=headers)

    log = _last_log(app, 'question.delete')
    assert log is not None
    assert log.resource_id == qid


# ── Subject CRUD ───────────────────────────────────────────────────────────────

def test_subject_write_operations_create_audit_logs(client, init_database, app):
    # Use an admin user who has subjects.create / update / delete
    from app.models.user import User
    from app.models.role import Role

    with app.app_context():
        admin_role = Role.query.filter_by(name='admin').first()
        admin = User(username='adminuser', email='admin@test.com')
        admin.set_password('admin1234')
        admin.roles = [admin_role]
        db.session.add(admin)
        db.session.commit()

    res = client.post('/api/auth/login', json={'email': 'admin@test.com', 'password': 'admin1234'})
    headers = {'Authorization': f'Bearer {res.get_json()["access_token"]}'}

    created = client.post('/api/subjects/', json={'name': 'Audit Subject', 'code': 'AUD1'}, headers=headers)
    sid = created.get_json()['subject']['id']
    log_create = _last_log(app, 'subject.create')
    assert log_create is not None and log_create.resource_id == sid

    client.put(f'/api/subjects/{sid}', json={'name': 'Audit Subject Updated'}, headers=headers)
    log_update = _last_log(app, 'subject.update')
    assert log_update is not None and log_update.resource_id == sid

    client.delete(f'/api/subjects/{sid}', headers=headers)
    log_delete = _last_log(app, 'subject.delete')
    assert log_delete is not None and log_delete.resource_id == sid


# ── to_dict ────────────────────────────────────────────────────────────────────

def test_audit_log_to_dict(client, init_database, app):
    client.post('/api/auth/login', json={'email': 'test@test.com', 'password': 'password123'})
    log = _last_log(app, 'auth.login')
    with app.app_context():
        d = db.session.get(AuditLog, log.id).to_dict()
    assert {'id', 'timestamp', 'user_id', 'action', 'resource_type',
            'resource_id', 'details', 'ip_address', 'status'} == set(d.keys())
