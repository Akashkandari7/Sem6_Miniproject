"""
RBAC authorization decorators.

Usage in routes (replaces @jwt_required())::

    from app.authorization import require_permission, require_role, get_current_user

    @bp.route('/', methods=['POST'])
    @require_permission('questions.create')
    def create_question():
        user = get_current_user()   # already loaded; no extra DB hit
        ...

Decorator call order is innermost-first (Python stacking), so these decorators
must be placed directly above the function, beneath the @route decorator::

    @bp.route('/admin-stuff')
    @require_role('admin')          # ← evaluated last  (outermost wrapper)
    @require_permission('users.list')  # ← evaluated first (innermost wrapper)
    def admin_endpoint():
        ...

If only one check is needed, one decorator is enough.  Never keep a bare
@jwt_required() alongside these — they call verify_jwt_in_request() themselves.
"""

from functools import wraps
from flask import jsonify, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.extensions import db


# ── Internal helpers ───────────────────────────────────────────────────────────

def _load_current_user():
    """
    Return the User for the current JWT identity.

    The result is cached on Flask's request-context ``g`` so that stacked
    decorators (and a subsequent ``get_current_user()`` call inside the route)
    issue at most **one** database query per request.
    """
    if not hasattr(g, '_rbac_user'):
        from app.models.user import User
        user_id = get_jwt_identity()
        g._rbac_user = db.session.get(User, int(user_id))
    return g._rbac_user


def _check_active(user):
    """
    Return a 401 response tuple when the user is missing or inactive,
    otherwise return None (meaning the check passed).
    """
    if not user or not user.is_active:
        return jsonify({'error': 'Account not found or inactive'}), 401
    return None


# ── Public helper ──────────────────────────────────────────────────────────────

def get_current_user():
    """
    Return the authenticated ``User`` object for the current request.

    Call this **inside** a route that is already protected by one of the
    decorators below — the user will already be cached on ``g`` so no
    additional database query is made.  Works correctly even if called
    before an RBAC decorator has run (e.g. in tests or non-decorated
    helpers), in which case it performs a fresh lookup.
    """
    return _load_current_user()


# ── Decorators ─────────────────────────────────────────────────────────────────

def require_permission(permission_name: str):
    """
    Decorator factory — grants access when the user holds *permission_name*.

    Responds with:
    - 401  if the JWT is missing / invalid, or the account is inactive
    - 403  if the user is authenticated but lacks the permission
    - (passes through) if the check succeeds

    Example::

        @papers_bp.route('/', methods=['POST'])
        @require_permission('papers.create')
        def create_paper():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = _load_current_user()

            inactive = _check_active(user)
            if inactive:
                return inactive

            if not user.has_permission(permission_name):
                from app.services.audit_service import log_action
                log_action('auth.permission_denied', status='failure',
                           details={'required_permission': permission_name})
                return jsonify({
                    'error': 'Forbidden',
                    'required_permission': permission_name,
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role_name: str):
    """
    Decorator factory — grants access when the user holds *role_name*.

    Use for coarse-grained admin gates. Prefer ``require_permission`` for
    fine-grained resource-level control.

    Responds with:
    - 401  if the JWT is missing / invalid, or the account is inactive
    - 403  if the user does not hold the role

    Example::

        @auth_bp.route('/users')
        @require_role('admin')
        def list_users():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = _load_current_user()

            inactive = _check_active(user)
            if inactive:
                return inactive

            if not user.has_role(role_name):
                from app.services.audit_service import log_action
                log_action('auth.permission_denied', status='failure',
                           details={'required_role': role_name})
                return jsonify({
                    'error': 'Forbidden',
                    'required_role': role_name,
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_any_role(*role_names: str):
    """
    Decorator factory — grants access when the user holds any one of the listed roles.

    Useful for endpoints accessible to both admins and teachers (e.g. shared profile).

    Responds with:
    - 401  if the JWT is missing / invalid, or the account is inactive
    - 403  if the user holds none of the listed roles
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = _load_current_user()

            inactive = _check_active(user)
            if inactive:
                return inactive

            if not any(user.has_role(role) for role in role_names):
                from app.services.audit_service import log_action
                log_action('auth.permission_denied', status='failure',
                           details={'required_any_of_roles': list(role_names)})
                return jsonify({
                    'error': 'Forbidden',
                    'required_any_of_roles': list(role_names),
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permission_names: str):
    """
    Decorator factory — grants access when the user holds **at least one**
    of the listed permissions.

    Useful for shared endpoints where multiple roles have different but
    overlapping access (e.g. both admin and teacher can view a resource).

    Responds with:
    - 401  if the JWT is missing / invalid, or the account is inactive
    - 403  if the user holds none of the listed permissions

    Example::

        @questions_bp.route('/', methods=['GET'])
        @require_any_permission('questions.read', 'questions.create')
        def get_questions():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = _load_current_user()

            inactive = _check_active(user)
            if inactive:
                return inactive

            user_perms = user.get_all_permissions()
            if not any(p in user_perms for p in permission_names):
                from app.services.audit_service import log_action
                log_action('auth.permission_denied', status='failure',
                           details={'required_any_of': list(permission_names)})
                return jsonify({
                    'error': 'Forbidden',
                    'required_any_of': list(permission_names),
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_all_permissions(*permission_names: str):
    """
    Decorator factory — grants access only when the user holds **every**
    listed permission.

    The 403 response includes which specific permissions are missing so
    callers can surface a meaningful error.

    Responds with:
    - 401  if the JWT is missing / invalid, or the account is inactive
    - 403  if one or more permissions are absent

    Example::

        @papers_bp.route('/<int:paper_id>/finalize', methods=['POST'])
        @require_all_permissions('papers.update', 'papers.download_pdf')
        def finalize_paper(paper_id):
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = _load_current_user()

            inactive = _check_active(user)
            if inactive:
                return inactive

            user_perms = user.get_all_permissions()
            missing = [p for p in permission_names if p not in user_perms]
            if missing:
                from app.services.audit_service import log_action
                log_action('auth.permission_denied', status='failure',
                           details={'missing_permissions': missing})
                return jsonify({
                    'error': 'Forbidden',
                    'missing_permissions': missing,
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator
