from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.paper import Paper
from app.models.question import Question
from app.models.subject import Subject
from app.services.paper_generator import generate_paper
from app.authorization import require_permission, get_current_user

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

    required = ['title', 'subject_id', 'total_marks', 'duration_minutes', 'config']
    if not all(k in data for k in required):
        return jsonify({'error': f'Required fields: {required}'}), 400

    if not db.session.get(Subject, data['subject_id']):
        return jsonify({'error': 'Subject not found'}), 404

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

    db.session.delete(paper)
    db.session.commit()

    return jsonify({'message': 'Paper deleted successfully'}), 200


@papers_bp.route('/<int:paper_id>', methods=['PUT'])
@require_permission('papers.update')
def update_paper(paper_id):
    """Update paper questions or details."""
    paper = db.get_or_404(Paper, paper_id)
    data = request.get_json()

    if 'title' in data:
        paper.title = data['title']

    if 'question_ids' in data:
        new_questions = Question.query.filter(Question.id.in_(data['question_ids'])).all()
        id_map = {q.id: q for q in new_questions}
        paper.questions  = [id_map[qid] for qid in data['question_ids'] if qid in id_map]
        paper.total_marks = sum(q.marks for q in paper.questions)

    db.session.commit()
    return jsonify({'message': 'Paper updated successfully', 'paper': paper.to_dict()}), 200


@papers_bp.route('/<int:paper_id>/pdf', methods=['GET'])
@require_permission('papers.download_pdf')
def download_paper_pdf(paper_id):
    """Generate and stream a PDF for a paper."""
    from flask import send_file
    from app.services.pdf_generator import generate_paper_pdf

    paper = db.get_or_404(Paper, paper_id)
    paper_data = paper.to_dict()
    paper_data['questions']    = [q.to_dict() for q in paper.questions]
    paper_data['subject_name'] = paper.subject.name if paper.subject else 'Examination'
    paper_data['subject_code'] = paper.subject.code if paper.subject else ''

    pdf_buffer = generate_paper_pdf(paper_data)

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{paper.title.replace(' ', '_')}.pdf",
    )
