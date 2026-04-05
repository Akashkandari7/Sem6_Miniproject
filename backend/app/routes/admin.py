from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User
from app.models.subject import Subject
from app.authorization import require_role, require_permission, get_current_user
from app.services.audit_service import log_action

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/teachers', methods=['GET'])
@require_permission('users.list')
@require_role('admin')
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
@require_permission('users.assign_subjects')
@require_role('admin')
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

@admin_bp.route('/subject-requests', methods=['GET'])
@require_role('admin')
def get_subject_requests():
    """List all teacher subject requests."""
    from app.models.subject_request import SubjectRequest
    status = request.args.get('status', 'pending')
    
    query = SubjectRequest.query
    if status != 'all':
        query = query.filter_by(status=status)
        
    reqs = query.order_by(SubjectRequest.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'data': [r.to_dict() for r in reqs],
        'count': len(reqs)
    }), 200

@admin_bp.route('/subject-requests/<int:request_id>/action', methods=['POST'])
@require_permission('users.assign_subjects')
@require_role('admin')
def handle_subject_request(request_id):
    """Approve or reject a subject request (access or new_subject)."""
    from app.models.subject_request import SubjectRequest
    data = request.get_json()
    action = data.get('action') # 'approve' or 'reject'
    notes  = data.get('notes', '')

    if action not in ['approve', 'reject']:
        return jsonify({'success': False, 'message': 'Invalid action. Use approve or reject.'}), 400

    req = db.get_or_404(SubjectRequest, request_id)
    if req.status != 'pending':
        return jsonify({'success': False, 'message': 'Request already processed'}), 400

    if action == 'approve':
        req.status = 'approved'
        ai_note = ''

        if req.request_type == 'new_subject':
            # ── Create the brand-new subject ──
            new_subject = Subject(
                name=req.subject_name,
                code=req.subject_code,
                description=req.subject_description or ''
            )
            db.session.add(new_subject)
            db.session.flush()  # get new_subject.id

            # Link the request to the created subject
            req.subject_id = new_subject.id

            # Assign subject to the requesting teacher
            if new_subject not in req.user.subjects:
                req.user.subjects.append(new_subject)

            # ── AI-generate 20 starter questions from the topics ──
            try:
                import os
                from app.services.ai_service import AIService
                from app.models.question import Question

                api_key = os.getenv('GOOGLE_API_KEY')
                if api_key:
                    ai_service = AIService(api_key=api_key)
                    topics = req.topics or req.subject_name

                    # Use smaller batch generation (5 questions) to avoid Vercel 10s timeout
                    distribution = {"1": 3, "3": 1, "5": 1}
                    generated = ai_service.generate_questions_batch(
                        subject_name=req.subject_name,
                        topic=topics,
                        distribution=distribution
                    )

                    saved_count = 0
                    for g in generated:
                        q = Question(
                            text=g.get('text', ''),
                            question_type=g.get('question_type', 'short'),
                            blooms_level=g.get('blooms_level', 'understand'),
                            difficulty=g.get('difficulty', 'medium'),
                            marks=int(g.get('marks', 1)),
                            option_a=g.get('option_a'),
                            option_b=g.get('option_b'),
                            option_c=g.get('option_c'),
                            option_d=g.get('option_d'),
                            correct_answer=g.get('correct_answer'),
                            subject_id=new_subject.id,
                            created_by=req.user_id,
                        )
                        db.session.add(q)
                        saved_count += 1

                    ai_note = f' | AI generated {saved_count} starter questions.'
                else:
                    ai_note = ' | AI skipped: No GOOGLE_API_KEY configured.'
            except Exception as e:
                ai_note = f' | AI generation failed: {str(e)}'
                print(f"AI seeding error for request {request_id}: {e}")

        else:
            # Existing flow: grant access to an existing subject
            if req.subject and req.subject not in req.user.subjects:
                req.user.subjects.append(req.subject)

        req.admin_notes = (notes + ai_note).strip()
    else:
        req.status = 'rejected'
        req.admin_notes = notes

    db.session.commit()

    log_action('admin.subject_request_action', resource_type='subject_request', resource_id=req.id,
               details={'action': action, 'user_id': req.user_id, 'request_type': req.request_type})

    return jsonify({
        'success': True,
        'message': f'Request {action}d successfully' + (ai_note if action == 'approve' else '')
    }), 200
  

@admin_bp.route('/support', methods=['GET'])
@require_role('admin')
def get_support_messages():
    """List all support tickets sent by teachers."""
    from app.models.support_message import SupportMessage
    status = request.args.get('status', 'pending')
    
    query = SupportMessage.query
    if status != 'all':
        query = query.filter_by(status=status)
        
    messages = query.order_by(SupportMessage.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'data': [m.to_dict() for m in messages],
        'count': len(messages)
    }), 200

@admin_bp.route('/support/<int:message_id>/resolve', methods=['POST'])
@require_role('admin')
def resolve_support_message(message_id):
    """Mark a support ticket as resolved."""
    from app.models.support_message import SupportMessage
    msg = db.get_or_404(SupportMessage, message_id)
    msg.status = 'resolved'
    db.session.commit()
    
    log_action('admin.support_resolve', resource_type='support_message', resource_id=message_id)
    return jsonify({'success': True, 'message': 'Ticket resolved successfully'}), 200
