from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.paper import Paper
from app.models.question import Question
from app.models.subject import Subject
from app.services.paper_generator import generate_paper
from app.authorization import require_permission, get_current_user
from app.services.audit_service import log_action

papers_bp = Blueprint('papers', __name__)


@papers_bp.route('/', methods=['GET'])
@require_permission('papers.read')
def get_papers():
    """Get all papers for the current user."""
    user_id = get_current_user().id
    papers = Paper.query.filter_by(created_by=user_id).all()
    return jsonify({
        'papers': [p.to_dict() for p in papers],
        'count': len(papers),
    }), 200


@papers_bp.route('/<int:paper_id>', methods=['GET'])
@require_permission('papers.read')
def get_paper(paper_id):
    """Get a single paper with all its questions."""
    paper = db.get_or_404(Paper, paper_id)
    user = get_current_user()

    # Security: Only creator or admin can view
    if paper.created_by != user.id and not user.has_role('admin'):
        return jsonify({'error': 'Forbidden', 'message': 'You do not own this paper'}), 403

    paper_data = paper.to_dict()
    paper_data['questions'] = [q.to_dict() for q in paper.questions]

    return jsonify({'paper': paper_data}), 200


@papers_bp.route('/generate', methods=['POST'])
@require_permission('papers.create')
def create_paper():
    """
    Generate a paper based on configuration.

    Expected body::

        {
            "title": "Mid Term Exam",
            "subject_id": 1,
            "total_marks": 100,
            "duration_minutes": 180,
            "config": {
                "blooms_distribution":  {"remember": 20, "understand": 30, "apply": 50},
                "difficulty_distribution": {"easy": 30, "medium": 50, "hard": 20},
                "question_type": "mixed"
            }
        }
    """
    data = request.get_json()

    required = ['title', 'subject_id', 'duration_minutes', 'config']
    if not all(k in data for k in required):
        missing = [k for k in required if k not in data]
        return jsonify({'error': f'Required fields: {missing}'}), 400

    if not db.session.get(Subject, data['subject_id']):
        return jsonify({'error': 'Subject not found'}), 404

    # Security: Verify teacher has access to this subject
    user = get_current_user()
    if not user.has_role('admin'):
        subject_ids = [s.id for s in user.subjects]
        if data['subject_id'] not in subject_ids:
            return jsonify({'error': 'Forbidden', 'message': 'You are not assigned to this subject'}), 403

    result = generate_paper(
        subject_id=data['subject_id'],
        total_marks=data['total_marks'],
        config=data['config'],
    )

    if not result['success']:
        return jsonify({'error': result['message']}), 400

    paper = Paper(
        title=data['title'],
        total_marks=result['total_marks_allocated'],
        duration_minutes=data['duration_minutes'],
        config=data['config'],
        subject_id=data['subject_id'],
        created_by=get_current_user().id,
    )

    db.session.add(paper)
    db.session.flush()  # get paper.id before commit

    for question in result['questions']:
        paper.questions.append(question)
        question.times_used = (question.times_used or 0) + 1

    db.session.commit()
    log_action('paper.create', resource_type='paper', resource_id=paper.id,
               details={'subject_id': data['subject_id'], 'total_marks': paper.total_marks,
                        'question_count': len(paper.questions)})

    paper_data = paper.to_dict()
    paper_data['questions'] = [q.to_dict() for q in paper.questions]

    return jsonify({
        'message': 'Paper generated successfully',
        'paper': paper_data,
    }), 201


@papers_bp.route('/<int:paper_id>', methods=['DELETE'])
@require_permission('papers.delete')
def delete_paper(paper_id):
    """Delete a paper."""
    paper = db.get_or_404(Paper, paper_id)
    user = get_current_user()

    # Security: Only creator or admin can delete
    if paper.created_by != user.id and not user.has_role('admin'):
        return jsonify({'error': 'Forbidden', 'message': 'You do not own this paper'}), 403

    db.session.delete(paper)
    db.session.commit()
    log_action('paper.delete', resource_type='paper', resource_id=paper_id)

    return jsonify({'message': 'Paper deleted successfully'}), 200


@papers_bp.route('/<int:paper_id>', methods=['PUT'])
@require_permission('papers.update')
def update_paper(paper_id):
    """Update paper questions or details."""
    paper = db.get_or_404(Paper, paper_id)
    user = get_current_user()

    # Security: Only creator or admin can update
    if paper.created_by != user.id and not user.has_role('admin'):
        return jsonify({'error': 'Forbidden', 'message': 'You do not own this paper'}), 403

    data = request.get_json()

    if 'title' in data:
        paper.title = data['title']

    if 'question_ids' in data:
        new_questions = Question.query.filter(Question.id.in_(data['question_ids'])).all()
        id_map = {q.id: q for q in new_questions}
        paper.questions  = [id_map[qid] for qid in data['question_ids'] if qid in id_map]
        paper.total_marks = sum(q.marks for q in paper.questions)

    db.session.commit()
    log_action('paper.update', resource_type='paper', resource_id=paper_id)
    return jsonify({'message': 'Paper updated successfully', 'paper': paper.to_dict()}), 200


@papers_bp.route('/<int:paper_id>/pdf', methods=['GET'])
@require_permission('papers.download_pdf')
def download_paper_pdf(paper_id):
    """Generate and stream a PDF for a paper."""
    from flask import send_file
    from app.services.pdf_generator import generate_paper_pdf

    paper = db.get_or_404(Paper, paper_id)
    user = get_current_user()

    # Security: Only creator or admin can download
    if paper.created_by != user.id and not user.has_role('admin'):
        return jsonify({'error': 'Forbidden', 'message': 'You do not own this paper'}), 403

    paper_data = paper.to_dict()
    paper_data['questions']    = [q.to_dict() for q in paper.questions]
    paper_data['subject_name'] = paper.subject.name if paper.subject else 'Examination'
    paper_data['subject_code'] = paper.subject.code if paper.subject else ''

    pdf_buffer = generate_paper_pdf(paper_data)

    log_action('paper.download_pdf', resource_type='paper', resource_id=paper_id)
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{paper.title.replace(' ', '_')}.pdf",
    )
@papers_bp.route('/generate-ai-syllabus', methods=['POST'])
@require_permission('papers.create')
def generate_ai_syllabus_paper():
    """
    Generate a full paper from a syllabus description using AI.
    Saves all questions to the database.
    """
    data = request.get_json()
    user = get_current_user()

    required = ['title', 'subject_id', 'syllabus', 'distribution', 'duration_minutes']
    if not all(k in data for k in required):
        return jsonify({'error': f'Required fields: {required}'}), 400

    subject = db.session.get(Subject, data['subject_id'])
    if not subject:
        return jsonify({'error': 'Subject not found'}), 404

    # Security: Verify teacher has access to this subject
    if not user.has_role('admin'):
        subject_ids = [s.id for s in user.subjects]
        if data['subject_id'] not in subject_ids:
            return jsonify({'error': 'Forbidden', 'message': 'You are not assigned to this subject'}), 403

    from app.services.ai_service import AIService
    try:
        # 1. Generate questions in batch
        ai_service = AIService()
        generated_data = ai_service.generate_questions_batch(
            subject_name=subject.name,
            topic=data['syllabus'],
            distribution=data['distribution']
        )

        # 2. Create Paper object
        paper = Paper(
            title=data['title'],
            total_marks=0, # Calculated after questions created
            duration_minutes=data['duration_minutes'],
            config={'syllabus_mode': True, 'topic': data['syllabus'], 'distribution': data['distribution']},
            subject_id=data['subject_id'],
            created_by=user.id
        )
        db.session.add(paper)
        db.session.flush()

        total_marks = 0
        # 3. Save Questions and link to Paper
        for q_data in generated_data:
            q = Question(
                text=q_data['text'],
                question_type=q_data.get('question_type', 'short'),
                blooms_level=q_data.get('blooms_level', 'understand'),
                difficulty=q_data.get('difficulty', 'medium'),
                marks=q_data.get('marks', 1),
                option_a=q_data.get('option_a'),
                option_b=q_data.get('option_b'),
                option_c=q_data.get('option_c'),
                option_d=q_data.get('option_d'),
                correct_answer=q_data.get('correct_answer'),
                subject_id=data['subject_id'],
                created_by=user.id
            )
            db.session.add(q)
            db.session.flush()
            
            paper.questions.append(q)
            total_marks += int(q.marks)

        paper.total_marks = total_marks
        db.session.commit()

        log_action('paper.create_ai_syllabus', resource_type='paper', resource_id=paper.id,
                   details={'subject_id': data['subject_id'], 'q_count': len(generated_data)})

        paper_data = paper.to_dict()
        paper_data['questions'] = [q.to_dict() for q in paper.questions]
        return jsonify({
            'success': True,
            'message': f'Paper generated with {len(generated_data)} new questions',
            'paper': paper_data
        }), 201

    except Exception as e:
        db.session.rollback()
        log_action('paper.create_ai_syllabus', status='failure', details={'error': str(e)})
        return jsonify({'error': f'AI Paper Generation failed: {str(e)}'}), 500
