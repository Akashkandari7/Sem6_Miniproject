from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.paper import Paper
from app.models.question import Question
from app.models.subject import Subject
from app.services.paper_generator import generate_paper

papers_bp = Blueprint('papers', __name__)


@papers_bp.route('/', methods=['GET'])
@jwt_required()
def get_papers():
    """Get all papers for current user"""
    user_id = get_jwt_identity()
    papers = Paper.query.filter_by(created_by=int(user_id)).all()
    return jsonify({
        'papers': [p.to_dict() for p in papers],
        'count': len(papers)
    }), 200


@papers_bp.route('/<int:paper_id>', methods=['GET'])
@jwt_required()
def get_paper(paper_id):
    """Get single paper with all its questions"""
    paper = Paper.query.get_or_404(paper_id)

    paper_data = paper.to_dict()
    paper_data['questions'] = [q.to_dict() for q in paper.questions]

    return jsonify({'paper': paper_data}), 200


@papers_bp.route('/generate', methods=['POST'])
@jwt_required()
def create_paper():
    """
    Generate a paper based on configuration.
    
    Expected body:
    {
        "title": "Mid Term Exam",
        "subject_id": 1,
        "total_marks": 100,
        "duration_minutes": 180,
        "config": {
            "blooms_distribution": {
                "remember": 20,
                "understand": 30,
                "apply": 50
            },
            "difficulty_distribution": {
                "easy": 30,
                "medium": 50,
                "hard": 20
            },
            "question_type": "mixed"   // 'mcq', 'short', 'long', 'mixed'
        }
    }
    """
    data = request.get_json()
    user_id = get_jwt_identity()

    # Validate required fields
    required = ['title', 'subject_id', 'total_marks', 'duration_minutes', 'config']
    if not all(k in data for k in required):
        return jsonify({'error': f'Required fields: {required}'}), 400

    # Check subject exists
    if not Subject.query.get(data['subject_id']):
        return jsonify({'error': 'Subject not found'}), 404

    # Call paper generator service
    result = generate_paper(
        subject_id=data['subject_id'],
        total_marks=data['total_marks'],
        config=data['config']
    )

    if not result['success']:
        return jsonify({'error': result['message']}), 400

    # Save paper to database
    paper = Paper(
        title=data['title'],
        total_marks=data['total_marks'],
        duration_minutes=data['duration_minutes'],
        config=data['config'],
        subject_id=data['subject_id'],
        created_by=int(user_id)
    )

    db.session.add(paper)
    db.session.flush()  # get paper.id before commit

    # Link selected questions to paper
    for question in result['questions']:
        paper.questions.append(question)
        question.times_used += 1  # track usage

    db.session.commit()

    paper_data = paper.to_dict()
    paper_data['questions'] = [q.to_dict() for q in paper.questions]

    return jsonify({
        'message': 'Paper generated successfully',
        'paper': paper_data
    }), 201


@papers_bp.route('/<int:paper_id>', methods=['DELETE'])
@jwt_required()
def delete_paper(paper_id):
    """Delete a paper"""
    paper = Paper.query.get_or_404(paper_id)

    db.session.delete(paper)
    db.session.commit()

    return jsonify({'message': 'Paper deleted successfully'}), 200