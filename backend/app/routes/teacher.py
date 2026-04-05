import os
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.question import Question
from app.models.subject import Subject
from app.authorization import require_permission, require_role, require_any_role, get_current_user
from app.services.audit_service import log_action

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/subjects', methods=['GET'])
@require_any_role('teacher', 'admin')
@require_permission('subjects.read')
def get_teacher_subjects():
    """Get subjects assigned to the current teacher."""
    user = get_current_user()
    if user.has_role('admin'):
        subjects = Subject.query.all()
    else:
        subjects = user.subjects
        
    return jsonify({
        'success': True,
        'data': [s.to_dict() for s in subjects],
        'count': len(subjects)
    }), 200

@teacher_bp.route('/questions', methods=['GET'])
@require_any_role('teacher', 'admin')
@require_permission('questions.read')
def get_teacher_questions():
    """Get questions for the current teacher's assigned subjects."""
    user = get_current_user()
    subject_ids = [s.id for s in user.subjects]
    
    if not subject_ids and not user.has_role('admin'):
        return jsonify({
            'success': True,
            'data': [],
            'count': 0,
            'message': 'No subjects assigned to this teacher'
        }), 200

    difficulty = request.args.get('difficulty')
    blooms_level = request.args.get('blooms_level')
    limit = request.args.get('limit', type=int, default=50)
    offset = request.args.get('offset', type=int, default=0)

    query = Question.query
    
    # Filter by subject if provided
    subject_id = request.args.get('subject_id', type=int)
    if subject_id:
        # Security: Verify teacher has access to this subject
        if not user.has_role('admin') and subject_id not in subject_ids:
            return jsonify({'success': False, 'message': 'Forbidden access to this subject'}), 403
        query = query.filter_by(subject_id=subject_id)
    elif not user.has_role('admin'):
        query = query.filter(Question.subject_id.in_(subject_ids))
        
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if blooms_level:
        query = query.filter_by(blooms_level=blooms_level)
        
    total_count = query.count()
    questions = query.offset(offset).limit(limit).all()

    return jsonify({
        'success': True,
        'data': [q.to_dict() for q in questions],
        'count': total_count
    }), 200

@teacher_bp.route('/questions', methods=['POST'])
@require_role('teacher')
@require_permission('questions.create')
def add_question():
    """Manual addition of a question for an assigned subject."""
    data = request.get_json()
    user = get_current_user()
    
    subject_id = data.get('subject_id')
    if subject_id not in [s.id for s in user.subjects] and not user.has_role('admin'):
        return jsonify({
            'success': False,
            'message': 'You are not assigned to this subject'
        }), 403

    required = ['text', 'question_type', 'blooms_level', 'difficulty', 'marks']
    if not all(k in data for k in required):
        return jsonify({
            'success': False,
            'message': f'Required fields: {required}'
        }), 400

    question = Question(
        text=data['text'],
        question_type=data['question_type'],
        blooms_level=data['blooms_level'],
        difficulty=data['difficulty'],
        marks=data['marks'],
        option_a=data.get('option_a'),
        option_b=data.get('option_b'),
        option_c=data.get('option_c'),
        option_d=data.get('option_d'),
        correct_answer=data.get('correct_answer'),
        subject_id=subject_id,
        created_by=user.id
    )

    db.session.add(question)
    db.session.commit()
    
    log_action('teacher.question.create', resource_type='question', resource_id=question.id,
               details={'subject_id': subject_id, 'manual': True})

    return jsonify({
        'success': True,
        'message': 'Question added successfully',
        'data': question.to_dict()
    }), 201

@teacher_bp.route('/questions/generate', methods=['POST'])
@require_role('teacher')
@require_permission('questions.generate_ai')
def generate_and_save_question():
    """Generate a question via AI and automatically save it to the DB."""
    data = request.get_json()
    user = get_current_user()
    
    subject_id = data.get('subject_id')
    topic = data.get('topic')
    difficulty = data.get('difficulty', 'medium')
    blooms_level = data.get('blooms_level', 'understand')
    question_type = data.get('question_type', 'mcq')
    marks = data.get('marks', 1)

    if not subject_id or not topic:
        return jsonify({
            'success': False,
            'message': 'subject_id and topic are required'
        }), 400

    # 1. Access Check
    if subject_id not in [s.id for s in user.subjects] and not user.has_role('admin'):
        return jsonify({
            'success': False,
            'message': 'You are not assigned to this subject'
        }), 403

    subject = db.session.get(Subject, subject_id)
    if not subject:
        return jsonify({'success': False, 'message': 'Subject not found'}), 404

    # 2. AI Generation
    from app.services.ai_service import AIService
    try:
        api_key = request.headers.get('X-Gemini-API-Key') or os.getenv('GOOGLE_API_KEY')
        ai_service = AIService(api_key=api_key)
        
        generated = ai_service.generate_question(
            subject_name=subject.name,
            topic=topic,
            question_type=question_type,
            difficulty=difficulty,
            marks=marks,
        )
        
        # 3. Automatic Save
        question = Question(
            text=generated['text'],
            question_type=question_type,
            blooms_level=blooms_level,
            difficulty=difficulty,
            marks=marks,
            option_a=generated.get('option_a'),
            option_b=generated.get('option_b'),
            option_c=generated.get('option_c'),
            option_d=generated.get('option_d'),
            correct_answer=generated.get('correct_answer'),
            subject_id=subject_id,
            created_by=user.id
        )
        
        db.session.add(question)
        db.session.commit()
        
        log_action('teacher.question.generate_ai', resource_type='question', resource_id=question.id,
                   details={'subject_id': subject_id, 'topic': topic})

        return jsonify({
            'success': True,
            'message': 'Question generated and saved successfully',
            'data': question.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'AI Generation failed: {str(e)}'
        }), 500

@teacher_bp.route('/requests/subject', methods=['POST'])
@require_role('teacher')
def request_subject_access():
    """Teacher requests access to a specific subject."""
    from app.models.subject_request import SubjectRequest
    data = request.get_json()
    user = get_current_user()
    subject_id = data.get('subject_id')

    if not subject_id:
        return jsonify({'success': False, 'message': 'subject_id is required'}), 400

    subject = db.session.get(Subject, subject_id)
    if not subject:
        return jsonify({'success': False, 'message': 'Subject not found'}), 404

    # Check if already assigned
    if subject_id in [s.id for s in user.subjects]:
        return jsonify({'success': False, 'message': 'You already have access to this subject'}), 400

    # Check if a pending request already exists
    existing = SubjectRequest.query.filter_by(user_id=user.id, subject_id=subject_id, status='pending').first()
    if existing:
        return jsonify({'success': False, 'message': 'Request already pending for this subject'}), 400

    req = SubjectRequest(user_id=user.id, subject_id=subject_id)
    db.session.add(req)
    db.session.commit()

    log_action('teacher.subject_request', resource_type='subject_request', resource_id=req.id,
               details={'subject_id': subject_id})

    return jsonify({
        'success': True,
        'message': 'Request submitted successfully',
        'data': req.to_dict()
    }), 201

@teacher_bp.route('/requests/new-subject', methods=['POST'])
@require_role('teacher')
def request_new_subject():
    """Teacher proposes a brand-new subject with topics for AI seeding."""
    from app.models.subject_request import SubjectRequest
    data = request.get_json()
    user = get_current_user()

    subject_name = (data.get('subject_name') or '').strip()
    subject_code = (data.get('subject_code') or '').strip()
    topics = (data.get('topics') or '').strip()
    description = (data.get('description') or '').strip()

    if not subject_name or not subject_code or not topics:
        return jsonify({'success': False, 'message': 'subject_name, subject_code, and topics are required'}), 400

    # Check if subject code or name already exists
    existing_subject = Subject.query.filter(
        db.or_(
            Subject.code == subject_code,
            Subject.name.ilike(subject_name)
        )
    ).first()

    if existing_subject:
        # Convert to an access request for the existing subject
        # Check if they already have access
        if existing_subject in user.subjects:
            return jsonify({'success': False, 'message': 'You already have access to this subject'}), 400
            
        # Check if pending request exists
        existing_req = SubjectRequest.query.filter_by(
            user_id=user.id, subject_id=existing_subject.id, status='pending'
        ).first()
        
        if existing_req:
            return jsonify({'success': False, 'message': 'You already have a pending request for this subject'}), 400

        req = SubjectRequest(
            user_id=user.id,
            request_type='access',
            subject_name=existing_subject.name,
            subject_code=existing_subject.code,
            subject_id=existing_subject.id,
        )
        db.session.add(req)
        db.session.commit()
        log_action('teacher.subject_request', resource_type='subject_request', resource_id=req.id,
                   details={'subject_id': existing_subject.id})
        return jsonify({
            'success': True,
            'message': f'Subject "{existing_subject.name}" already exists. Access request sent to Admin.',
            'data': req.to_dict()
        }), 201

    # Otherwise, it's a completely new subject request
    existing_req = SubjectRequest.query.filter_by(
        user_id=user.id, subject_code=subject_code, request_type='new_subject', status='pending'
    ).first()
    if existing_req:
        return jsonify({'success': False, 'message': 'You already have a pending request for this subject code'}), 400

    req = SubjectRequest(
        user_id=user.id,
        request_type='new_subject',
        subject_name=subject_name,
        subject_code=subject_code,
        subject_description=description,
        topics=topics,
        subject_id=None,
    )
    db.session.add(req)
    db.session.commit()

    log_action('teacher.new_subject_request', resource_type='subject_request', resource_id=req.id,
               details={'subject_name': subject_name, 'subject_code': subject_code, 'topics': topics})

    return jsonify({
        'success': True,
        'message': 'New subject request submitted successfully. Admin will review it.',
        'data': req.to_dict()
    }), 201

@teacher_bp.route('/requests', methods=['GET'])
@require_role('teacher')
def get_my_requests():
    """Get all subject requests made by the current teacher."""
    from app.models.subject_request import SubjectRequest
    user = get_current_user()
    reqs = SubjectRequest.query.filter_by(user_id=user.id).order_by(SubjectRequest.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'data': [r.to_dict() for r in reqs]
    }), 200


@teacher_bp.route('/profile', methods=['GET'])
@require_any_role('teacher', 'admin')
def get_profile():
    """Get extended profile for the current teacher."""
    from app.models.paper import Paper
    user = get_current_user()
    
    # Get some stats
    paper_count = Paper.query.filter_by(created_by=user.id).count()
    question_count = Question.query.filter_by(created_by=user.id).count()
    
    return jsonify({
        'success': True,
        'data': {
            'user': user.to_dict(),
            'stats': {
                'papers': paper_count,
                'questions': question_count,
                'subjects': len(user.subjects)
            },
            'subjects': [s.to_dict() for s in user.subjects]
        }
    }), 200


@teacher_bp.route('/support', methods=['POST'])
@require_role('teacher')
def submit_support_request():
    """Teacher submits a help/support message to admin."""
    from app.models.support_message import SupportMessage
    data = request.get_json()
    user = get_current_user()

    subject = data.get('subject')
    message = data.get('message')

    if not subject or not message:
        return jsonify({'success': False, 'message': 'Subject and message are required'}), 400

    msg = SupportMessage(user_id=user.id, subject=subject, message=message)
    db.session.add(msg)
    db.session.commit()

    log_action('teacher.support_request', resource_type='support_message', resource_id=msg.id)

    return jsonify({
        'success': True,
        'message': 'Support request submitted. Admin will be notified.',
        'data': msg.to_dict()
    }), 201
