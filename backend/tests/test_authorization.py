"""
Tests for app/authorization.py

Each decorator is tested against four cases:
  - authenticated user WITH the required permission / role   → 200
  - authenticated user WITHOUT the required permission / role → 403
  - request with no JWT at all                               → 401
  - authenticated but inactive user                          → 401

get_current_user() caching is verified separately.
"""

import pytest
from flask import jsonify
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User


# ── Helpers ────────────────────────────────────────────────────────────────────

def _token(app, user_id: int) -> str:
    """Mint a JWT for *user_id* inside an app context."""
    with app.app_context():
        return create_access_token(identity=str(user_id))


def _auth(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def rbac_data(app):
    """
    Seed a minimal but complete RBAC dataset:

    Permissions
    -----------
    questions.create  questions.read  questions.delete

    Roles
    -----
    admin   → create + read + delete
    teacher → create + read
    viewer  → read only

    Users
    -----
    admin_user    ← admin role
    teacher_user  ← teacher role
    viewer_user   ← viewer role
    noroles_user  ← no roles at all
    inactive_user ← teacher role but is_active=False
    """
    with app.app_context():
        p_create = Permission(name='questions.create', resource='questions', action='create')
        p_read   = Permission(name='questions.read',   resource='questions', action='read')
        p_delete = Permission(name='questions.delete', resource='questions', action='delete')
        db.session.add_all([p_create, p_read, p_delete])

        r_admin   = Role(name='admin',   description='All perms')
        r_teacher = Role(name='teacher', description='Create + read')
        r_viewer  = Role(name='viewer',  description='Read only')

        r_admin.permissions   = [p_create, p_read, p_delete]
        r_teacher.permissions = [p_create, p_read]
        r_viewer.permissions  = [p_read]
        db.session.add_all([r_admin, r_teacher, r_viewer])

        def _user(username, email, roles, active=True):
            u = User(username=username, email=email, is_active=active)
            u.set_password('pw')
            u.roles = roles
            db.session.add(u)
            return u

        admin_u    = _user('adm',      'adm@t.com',   [r_admin])
        teacher_u  = _user('tea',      'tea@t.com',   [r_teacher])
        viewer_u   = _user('vie',      'vie@t.com',   [r_viewer])
        noroles_u  = _user('nor',      'nor@t.com',   [])
        inactive_u = _user('ina',      'ina@t.com',   [r_teacher], active=False)

        db.session.commit()

        yield {
            'admin_id':    admin_u.id,
            'teacher_id':  teacher_u.id,
            'viewer_id':   viewer_u.id,
            'noroles_id':  noroles_u.id,
            'inactive_id': inactive_u.id,
        }


@pytest.fixture
def rbac_client(app, rbac_data):
    """
    Register one test route per decorator variant, then return a test client.

    Routes are registered inside the fixture so they get a fresh endpoint name
    per app instance (each test gets its own app from the function-scoped
    ``app`` fixture, so there's no duplicate-registration error).
    """
    from app.authorization import (
        require_permission,
        require_role,
        require_any_permission,
        require_all_permissions,
        get_current_user,
    )

    # require_permission — needs 'questions.create'
    @app.route('/_t/perm')
    @require_permission('questions.create')
    def _t_perm():
        return jsonify({'ok': True})

    # require_role — needs 'admin'
    @app.route('/_t/role')
    @require_role('admin')
    def _t_role():
        return jsonify({'ok': True})

    # require_any_permission — needs 'questions.delete' OR 'questions.read'
    @app.route('/_t/any')
    @require_any_permission('questions.delete', 'questions.read')
    def _t_any():
        return jsonify({'ok': True})

    # require_all_permissions — needs BOTH 'questions.create' AND 'questions.delete'
    @app.route('/_t/all')
    @require_all_permissions('questions.create', 'questions.delete')
    def _t_all():
        return jsonify({'ok': True})

    # get_current_user — protected by require_permission, returns username
    @app.route('/_t/whoami')
    @require_permission('questions.read')
    def _t_whoami():
        user = get_current_user()   # must reuse cached g._rbac_user
        return jsonify({'username': user.username})

    return app.test_client()


# ── require_permission ─────────────────────────────────────────────────────────

class TestRequirePermission:

    def test_allows_user_with_permission(self, app, rbac_client, rbac_data):
        # teacher has questions.create
        res = rbac_client.get('/_t/perm',
                              headers=_auth(_token(app, rbac_data['teacher_id'])))
        assert res.status_code == 200

    def test_allows_admin_with_permission(self, app, rbac_client, rbac_data):
        res = rbac_client.get('/_t/perm',
                              headers=_auth(_token(app, rbac_data['admin_id'])))
        assert res.status_code == 200

    def test_denies_user_missing_permission(self, app, rbac_client, rbac_data):
        # viewer only has questions.read, not questions.create
        res = rbac_client.get('/_t/perm',
                              headers=_auth(_token(app, rbac_data['viewer_id'])))
        assert res.status_code == 403
        body = res.get_json()
        assert body['error'] == 'Forbidden'
        assert body['required_permission'] == 'questions.create'

    def test_denies_user_with_no_roles(self, app, rbac_client, rbac_data):
        res = rbac_client.get('/_t/perm',
                              headers=_auth(_token(app, rbac_data['noroles_id'])))
        assert res.status_code == 403

    def test_denies_unauthenticated_request(self, app, rbac_client, rbac_data):
        res = rbac_client.get('/_t/perm')
        assert res.status_code == 401

    def test_denies_inactive_user(self, app, rbac_client, rbac_data):
        # inactive_user has teacher role (would normally pass), but is_active=False
        res = rbac_client.get('/_t/perm',
                              headers=_auth(_token(app, rbac_data['inactive_id'])))
        assert res.status_code == 401
        assert 'inactive' in res.get_json()['error'].lower()


# ── require_role ───────────────────────────────────────────────────────────────

class TestRequireRole:

    def test_allows_user_with_correct_role(self, app, rbac_client, rbac_data):
        res = rbac_client.get('/_t/role',
                              headers=_auth(_token(app, rbac_data['admin_id'])))
        assert res.status_code == 200

    def test_denies_user_with_different_role(self, app, rbac_client, rbac_data):
        res = rbac_client.get('/_t/role',
                              headers=_auth(_token(app, rbac_data['teacher_id'])))
        assert res.status_code == 403
        body = res.get_json()
        assert body['error'] == 'Forbidden'
        assert body['required_role'] == 'admin'

    def test_denies_user_with_no_roles(self, app, rbac_client, rbac_data):
        res = rbac_client.get('/_t/role',
                              headers=_auth(_token(app, rbac_data['noroles_id'])))
        assert res.status_code == 403

    def test_denies_unauthenticated_request(self, app, rbac_client, rbac_data):
        res = rbac_client.get('/_t/role')
        assert res.status_code == 401

    def test_denies_inactive_user(self, app, rbac_client, rbac_data):
        res = rbac_client.get('/_t/role',
                              headers=_auth(_token(app, rbac_data['inactive_id'])))
        assert res.status_code == 401


# ── require_any_permission ─────────────────────────────────────────────────────

class TestRequireAnyPermission:
    # Route requires 'questions.delete' OR 'questions.read'

    def test_allows_user_with_one_matching_permission(self, app, rbac_client, rbac_data):
        # viewer has only questions.read — that matches
        res = rbac_client.get('/_t/any',
                              headers=_auth(_token(app, rbac_data['viewer_id'])))
        assert res.status_code == 200

    def test_allows_user_with_multiple_matching_permissions(self, app, rbac_client, rbac_data):
        # admin has both questions.delete and questions.read
        res = rbac_client.get('/_t/any',
                              headers=_auth(_token(app, rbac_data['admin_id'])))
        assert res.status_code == 200

    def test_denies_user_with_no_matching_permission(self, app, rbac_client, rbac_data):
        # noroles_user has no permissions at all
        res = rbac_client.get('/_t/any',
                              headers=_auth(_token(app, rbac_data['noroles_id'])))
        assert res.status_code == 403
        body = res.get_json()
        assert body['error'] == 'Forbidden'
        assert set(body['required_any_of']) == {'questions.delete', 'questions.read'}

    def test_denies_unauthenticated_request(self, app, rbac_client, rbac_data):
        res = rbac_client.get('/_t/any')
        assert res.status_code == 401

    def test_denies_inactive_user(self, app, rbac_client, rbac_data):
        res = rbac_client.get('/_t/any',
                              headers=_auth(_token(app, rbac_data['inactive_id'])))
        assert res.status_code == 401


# ── require_all_permissions ────────────────────────────────────────────────────

class TestRequireAllPermissions:
    # Route requires BOTH 'questions.create' AND 'questions.delete'

    def test_allows_user_with_all_permissions(self, app, rbac_client, rbac_data):
        # admin has create + read + delete
        res = rbac_client.get('/_t/all',
                              headers=_auth(_token(app, rbac_data['admin_id'])))
        assert res.status_code == 200

    def test_denies_user_missing_one_permission(self, app, rbac_client, rbac_data):
        # teacher has create but NOT delete
        res = rbac_client.get('/_t/all',
                              headers=_auth(_token(app, rbac_data['teacher_id'])))
        assert res.status_code == 403
        body = res.get_json()
        assert body['error'] == 'Forbidden'
        assert body['missing_permissions'] == ['questions.delete']

    def test_denies_user_missing_all_permissions(self, app, rbac_client, rbac_data):
        # viewer has only read — missing both create and delete
        res = rbac_client.get('/_t/all',
                              headers=_auth(_token(app, rbac_data['viewer_id'])))
        assert res.status_code == 403
        body = res.get_json()
        assert set(body['missing_permissions']) == {'questions.create', 'questions.delete'}

    def test_denies_unauthenticated_request(self, app, rbac_client, rbac_data):
        res = rbac_client.get('/_t/all')
        assert res.status_code == 401

    def test_denies_inactive_user(self, app, rbac_client, rbac_data):
        res = rbac_client.get('/_t/all',
                              headers=_auth(_token(app, rbac_data['inactive_id'])))
        assert res.status_code == 401


# ── get_current_user() + per-request caching ──────────────────────────────────

class TestGetCurrentUser:

    def test_returns_correct_user(self, app, rbac_client, rbac_data):
        res = rbac_client.get('/_t/whoami',
                              headers=_auth(_token(app, rbac_data['viewer_id'])))
        assert res.status_code == 200
        assert res.get_json()['username'] == 'vie'

    def test_user_cached_on_g(self, app, rbac_data):
        """
        Within a single request context, _load_current_user() must not issue
        more than one DB query.  We verify the cache by confirming the same
        object is returned on repeated calls.
        """
        from app.authorization import get_current_user

        with app.test_request_context('/'):
            # Manually push a JWT identity so get_jwt_identity() works
            with app.test_client() as c:
                token = _token(app, rbac_data['viewer_id'])
                with c.application.test_request_context(
                    '/', headers=_auth(token)
                ):
                    from flask_jwt_extended import verify_jwt_in_request
                    verify_jwt_in_request()

                    user_first  = get_current_user()
                    user_second = get_current_user()

                    # Same Python object — pulled from g, not re-queried
                    assert user_first is user_second
                    assert user_first.username == 'vie'
