import os
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.question import Question
from app.models.subject import Subject
from app.authorization import require_role, require_permission, get_current_user
from app.services.audit_service import log_action

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/subjects', methods=['GET'])
@require_role('teacher')
@require_permission('subjects.read')
def get_teacher_subjects():
    """Get subjects assigned to the current teacher."""
    user = get_current_user()
    return jsonify({
        'success': True,
        'data': [s.to_dict() for s in user.subjects],
        'count': len(user.subjects)
    }), 200

@teacher_bp.route('/questions', methods=['GET'])
@require_role('teacher')
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
    if not user.has_role('admin'):
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
