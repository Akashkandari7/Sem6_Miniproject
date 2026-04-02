from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User
from app.models.subject import Subject
from app.authorization import require_role, require_permission, get_current_user
from app.services.audit_service import log_action

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/teachers', methods=['GET'])
@require_role('admin')
@require_permission('users.list')
def get_teachers():
    """List all users with the 'teacher' role."""
    # Find the teacher role
    from app.models.role import Role
    teacher_role = Role.query.filter_by(name='teacher').first()
    
    if not teacher_role:
        return jsonify({
            'success': False,
            'message': 'Teacher role not found in system',
            'teachers': []
        }), 404

    # Get users who have this role
    teachers = [u for u in User.query.all() if teacher_role in u.roles]
    
    return jsonify({
        'success': True,
        'teachers': [t.to_dict() for t in teachers],
        'count': len(teachers)
    }), 200

@admin_bp.route('/assign-subjects', methods=['POST'])
@require_role('admin')
@require_permission('users.assign_subjects')
def assign_subjects():
    """
    Assign subjects to a teacher. 
    Expects JSON: { "teacher_id": 123, "subject_ids": [1, 2, 3] }
    """
    data = request.get_json()
    
    teacher_id = data.get('teacher_id')
    subject_ids = data.get('subject_ids')
    
    if teacher_id is None or subject_ids is None:
        return jsonify({
            'success': False,
            'message': 'teacher_id and subject_ids (list) are required'
        }), 400

    # 1. Validate Teacher
    teacher = db.session.get(User, teacher_id)
    if not teacher:
        return jsonify({
            'success': False,
            'message': f'User with ID {teacher_id} not found'
        }), 404
    
    if not teacher.has_role('teacher'):
        return jsonify({
            'success': False,
            'message': 'Selected user is not a teacher'
        }), 400

    # 2. Validate Subjects
    if not isinstance(subject_ids, list):
        return jsonify({
            'success': False,
            'message': 'subject_ids must be a list'
        }), 400

    new_subjects = []
    if subject_ids:
        # Prevent duplicates in the input list
        unique_ids = list(set(subject_ids))
        new_subjects = Subject.query.filter(Subject.id.in_(unique_ids)).all()
        
        if len(new_subjects) != len(unique_ids):
            return jsonify({
                'success': False,
                'message': 'One or more subject IDs are invalid'
            }), 400

    # 3. Apply changes (Replace existing)
    teacher.subjects = new_subjects
    
    try:
        db.session.commit()
        
        # 4. Audit Logging
        admin_user = get_current_user()
        log_action(
            action='users.assign_subjects',
            resource_type='user',
            resource_id=teacher.id,
            details={
                'admin_id': admin_user.id,
                'teacher_email': teacher.email,
                'subject_ids': [s.id for s in new_subjects],
                'subject_names': [s.name for s in new_subjects]
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'Subjects assigned successfully',
            'data': {
                'teacher_id': teacher.id,
                'subjects': [s.to_dict() for s in new_subjects]
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Database error: {str(e)}'
        }), 500
