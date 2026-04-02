from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.extensions import db
from app.models.user import User
from app.authorization import require_permission, get_current_user
from app.services.audit_service import log_action

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not all(k in data for k in ['username', 'email', 'password']):
        return jsonify({'error': 'username, email and password are required'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 409

    from app.models.role import Role
    user = User(
        username=data['username'],
        email=data['email'],
    )
    user.set_password(data['password'])
    teacher_role = Role.query.filter_by(name='teacher').first()
    if teacher_role:
        user.roles = [teacher_role]

    db.session.add(user)
    db.session.commit()
    log_action('auth.register', resource_type='user', resource_id=user.id,
               details={'username': user.username}, user_id=user.id)

    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not all(k in data for k in ['email', 'password']):
        return jsonify({'error': 'email and password are required'}), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['password']):
        log_action('auth.login', status='failure', details={'email': data['email']})
        return jsonify({'error': 'Invalid email or password'}), 401

    access_token = create_access_token(identity=str(user.id))
    log_action('auth.login', user_id=user.id)

    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/me', methods=['GET'])
@require_permission('users.read_self')
def me():
    """Get current logged-in user info."""
    return jsonify({'user': get_current_user().to_dict()}), 200
