import os
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.question import Question
from app.models.subject import Subject
from app.authorization import require_permission, get_current_user
from app.services.audit_service import log_action

questions_bp = Blueprint('questions', __name__)

VALID_BLOOMS = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
VALID_DIFFICULTY = ['easy', 'medium', 'hard']
VALID_TYPES = ['mcq', 'short', 'long']


@questions_bp.route('/', methods=['GET'])
@require_permission('questions.read')
def get_questions():
    """Get questions. Teachers are automatically filtered to their assigned subjects."""
    user = get_current_user()
    subject_id    = request.args.get('subject_id', type=int)
    blooms_level  = request.args.get('blooms_level')
    difficulty    = request.args.get('difficulty')
    question_type = request.args.get('question_type')

    query = Question.query

    # Security: If teacher and NOT admin, restrict query to assigned subjects
    if user.has_role('teacher') and not user.has_role('admin'):
        subject_ids = [s.id for s in user.subjects]
        if not subject_ids:
            return jsonify({'questions': [], 'count': 0, 'message': 'No subjects assigned'}), 200
        
        # If they requested a specific subject_id, verify they have access to it
        if subject_id:
            if subject_id not in subject_ids:
                return jsonify({'error': 'Forbidden', 'message': 'You do not have access to this subject'}), 403
            query = query.filter_by(subject_id=subject_id)
        else:
            # Otherwise, show all questions from ALL their assigned subjects
            query = query.filter(Question.subject_id.in_(subject_ids))
    elif subject_id:
        # Admin or other role can filter as they wish
        query = query.filter_by(subject_id=subject_id)

    # Apply other filters
    if blooms_level:
        query = query.filter_by(blooms_level=blooms_level)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if question_type:
        query = query.filter_by(question_type=question_type)

    questions = query.all()

    return jsonify({
        'questions': [q.to_dict() for q in questions],
        'count': len(questions),
    }), 200


@questions_bp.route('/my-subjects', methods=['GET'])
@require_permission('questions.read')
def get_my_questions():
    """Get questions only for subjects assigned to the current teacher."""
    user = get_current_user()
    
    # Extract subject IDs from teacher_subjects
    subject_ids = [s.id for s in user.subjects]
    
    if not subject_ids and not user.has_role('admin'):
        return jsonify({
            'success': True,
            'data': [],
            'count': 0,
            'message': 'No subjects assigned to this teacher'
        }), 200

    # Filtering parameters
    blooms_level  = request.args.get('blooms_level')
    difficulty    = request.args.get('difficulty')
    limit         = request.args.get('limit', type=int, default=50)
    offset        = request.args.get('offset', type=int, default=0)

    # Base query: filter by subject_id list
    query = Question.query
    if not user.has_role('admin'):
        query = query.filter(Question.subject_id.in_(subject_ids))
    
    # Optional filters
    if blooms_level:
        query = query.filter_by(blooms_level=blooms_level)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
        
    total_count = query.count()
    questions = query.offset(offset).limit(limit).all()

    return jsonify({
        'success': True,
        'data': [q.to_dict() for q in questions],
        'count': total_count,
        'limit': limit,
        'offset': offset
    }), 200


@questions_bp.route('/<int:question_id>', methods=['GET'])
@require_permission('questions.read')
def get_question(question_id):
    """Get a single question by ID with security check."""
    question = db.get_or_404(Question, question_id)
    user = get_current_user()
    
    # Security: If not admin, verify subject access
    if not user.has_role('admin'):
        subject_ids = [s.id for s in user.subjects]
        if question.subject_id not in subject_ids:
            return jsonify({
                'error': 'Forbidden',
                'message': 'You do not have access to questions from this subject'
            }), 403
            
    return jsonify({'question': question.to_dict()}), 200


@questions_bp.route('/', methods=['POST'])
@require_permission('questions.create')
def create_question():
    """Create a new question."""
    data = request.get_json()

    required = ['text', 'question_type', 'blooms_level', 'difficulty', 'marks', 'subject_id']
    if not all(k in data for k in required):
        return jsonify({'error': f'Required fields: {required}'}), 400

    if data['blooms_level'] not in VALID_BLOOMS:
        return jsonify({'error': f'blooms_level must be one of {VALID_BLOOMS}'}), 400

    if data['difficulty'] not in VALID_DIFFICULTY:
        return jsonify({'error': f'difficulty must be one of {VALID_DIFFICULTY}'}), 400

    if data['question_type'] not in VALID_TYPES:
        return jsonify({'error': f'question_type must be one of {VALID_TYPES}'}), 400

    if not db.session.get(Subject, data['subject_id']):
        return jsonify({'error': 'Subject not found'}), 404

    # Security: Verify teacher has access to this subject
    user = get_current_user()
    if not user.has_role('admin'):
        subject_ids = [s.id for s in user.subjects]
        if data['subject_id'] not in subject_ids:
            return jsonify({'error': 'Forbidden', 'message': 'You are not assigned to this subject'}), 403

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
        subject_id=data['subject_id'],
        created_by=get_current_user().id,
    )

    db.session.add(question)
    db.session.commit()
    log_action('question.create', resource_type='question', resource_id=question.id,
               details={'subject_id': question.subject_id, 'question_type': question.question_type})

    return jsonify({
        'message': 'Question created successfully',
        'question': question.to_dict(),
    }), 201


@questions_bp.route('/<int:question_id>', methods=['PUT'])
@require_permission('questions.update')
def update_question(question_id):
    """Update an existing question."""
    question = db.get_or_404(Question, question_id)
    user = get_current_user()

    # Security: Only creator or admin can update
    if question.created_by != user.id and not user.has_role('admin'):
        return jsonify({'error': 'Forbidden', 'message': 'You do not own this question'}), 403

    data = request.get_json()

    question.text          = data.get('text',           question.text)
    question.blooms_level  = data.get('blooms_level',   question.blooms_level)
    question.difficulty    = data.get('difficulty',     question.difficulty)
    question.marks         = data.get('marks',          question.marks)
    question.option_a      = data.get('option_a',       question.option_a)
    question.option_b      = data.get('option_b',       question.option_b)
    question.option_c      = data.get('option_c',       question.option_c)
    question.option_d      = data.get('option_d',       question.option_d)
    question.correct_answer = data.get('correct_answer', question.correct_answer)

    db.session.commit()
    log_action('question.update', resource_type='question', resource_id=question.id)

    return jsonify({
        'message': 'Question updated successfully',
        'question': question.to_dict(),
    }), 200


@questions_bp.route('/generate-ai', methods=['POST'])
@require_permission('questions.generate_ai')
def generate_ai_question():
    """Generate a question using AI and return it (without saving)."""
    data = request.get_json()

    subject_id    = data.get('subject_id')
    topic         = data.get('topic')
    question_type = data.get('question_type', 'mcq')
    difficulty    = data.get('difficulty', 'medium')
    marks         = data.get('marks', 1)

    api_key = (
        data.get('api_key')
        or request.headers.get('X-Gemini-API-Key')
        or os.getenv('GOOGLE_API_KEY')
    )

    if not subject_id or not topic:
        return jsonify({'error': 'subject_id and topic are required'}), 400

    subject = db.session.get(Subject, subject_id)
    if not subject:
        return jsonify({'error': 'Subject not found'}), 404

    # Security: Verify teacher has access to this subject
    user = get_current_user()
    if not user.has_role('admin'):
        subject_ids = [s.id for s in user.subjects]
        if subject_id not in subject_ids:
            return jsonify({'error': 'Forbidden', 'message': 'You are not assigned to this subject'}), 403

    from app.services.ai_service import AIService
    try:
        ai_service = AIService(api_key=api_key)
        generated = ai_service.generate_question(
            subject_name=subject.name,
            topic=topic,
            question_type=question_type,
            difficulty=difficulty,
            marks=marks,
        )
        generated.setdefault('subject_id',    subject_id)
        generated.setdefault('question_type', question_type)
        generated.setdefault('difficulty',    difficulty)
        generated.setdefault('marks',         marks)
        generated.setdefault('blooms_level',  'understand')

        log_action('question.generate_ai', details={'subject_id': subject_id, 'topic': topic,
                                                    'question_type': question_type})
        return jsonify({
            'message': 'AI question generated successfully',
            'question': generated,
        }), 200
    except ValueError as ve:
        log_action('question.generate_ai', status='failure',
                   details={'subject_id': subject_id, 'topic': topic, 'error': str(ve)})
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        log_action('question.generate_ai', status='failure',
                   details={'subject_id': subject_id, 'topic': topic, 'error': str(e)})
        return jsonify({'error': f'AI generation failed: {str(e)}'}), 500


@questions_bp.route('/<int:question_id>', methods=['DELETE'])
@require_permission('questions.delete')
def delete_question(question_id):
    """Delete a question."""
    question = db.get_or_404(Question, question_id)
    user = get_current_user()

    # Security: Only creator or admin can delete
    if question.created_by != user.id and not user.has_role('admin'):
        return jsonify({'error': 'Forbidden', 'message': 'You do not own this question'}), 403

    db.session.delete(question)
    db.session.commit()
    log_action('question.delete', resource_type='question', resource_id=question_id)

    return jsonify({'message': 'Question deleted successfully'}), 200


@questions_bp.route('/bulk', methods=['POST'])
@require_permission('questions.create')
def bulk_upload_questions():
    """
    Upload questions in bulk via CSV or Excel.
    Expected headers: subject_id, text, marks, topic, question_type, difficulty, blooms_level
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    import pandas as pd
    import io

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file.read()))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(file.read()))
        else:
            return jsonify({'error': 'Unsupported file format. Use CSV or Excel.'}), 400

        # Basic validation of required columns
        required_cols = ['subject_id', 'text', 'marks']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return jsonify({'error': f'Missing required columns: {missing}'}), 400

        user = get_current_user()
        user_id = user.id
        count = 0
        skipped_rows = []
        
        # Determine allowed subjects for security check
        if not user.has_role('admin'):
            assigned_sids = set(s.id for s in user.subjects)
        else:
            assigned_sids = None # Admin can do anything

        for row_idx, row in df.iterrows():
            sid = int(row['subject_id'])
            
            # Security: check if teacher is assigned to this subject
            if assigned_sids is not None and sid not in assigned_sids:
                skipped_rows.append({'row': int(row_idx) + 2, 'subject_id': sid, 'reason': 'Not assigned to this subject'})
                continue 

            q = Question(
                text=str(row['text']),
                marks=int(row['marks']),
                subject_id=sid,
                topic=str(row.get('topic', '')),
                question_type=str(row.get('question_type', 'short')),
                difficulty=str(row.get('difficulty', 'medium')),
                blooms_level=str(row.get('blooms_level', 'understand')),
                created_by=user_id,
                option_a=str(row['option_a']) if 'option_a' in row and pd.notna(row['option_a']) else None,
                option_b=str(row['option_b']) if 'option_b' in row and pd.notna(row['option_b']) else None,
                option_c=str(row['option_c']) if 'option_c' in row and pd.notna(row['option_c']) else None,
                option_d=str(row['option_d']) if 'option_d' in row and pd.notna(row['option_d']) else None,
                correct_answer=str(row['correct_answer']) if 'correct_answer' in row and pd.notna(row['correct_answer']) else None
            )
            db.session.add(q)
            count += 1

        db.session.commit()
        log_action('questions.bulk_upload', details={'count': count, 'skipped': len(skipped_rows)})
        
        response = {
            'success': True,
            'message': f'Successfully uploaded {count} questions',
            'count': count
        }
        if skipped_rows:
            response['warning'] = f'{len(skipped_rows)} row(s) skipped due to unauthorized subject access'
            response['skipped_rows'] = skipped_rows
        
        return jsonify(response), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Bulk upload failed: {str(e)}'}), 500
