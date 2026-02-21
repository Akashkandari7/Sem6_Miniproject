from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.question import Question
from app.models.subject import Subject

questions_bp = Blueprint('questions', __name__)

VALID_BLOOMS = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
VALID_DIFFICULTY = ['easy', 'medium', 'hard']
VALID_TYPES = ['mcq', 'short', 'long']


@questions_bp.route('/', methods=['GET'])
@jwt_required()
def get_questions():
    """Get all questions with optional filters"""
    subject_id = request.args.get('subject_id', type=int)
    blooms_level = request.args.get('blooms_level')
    difficulty = request.args.get('difficulty')
    question_type = request.args.get('question_type')

    query = Question.query

    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if blooms_level:
        query = query.filter_by(blooms_level=blooms_level)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if question_type:
        query = query.filter_by(question_type=question_type)

    questions = query.all()

    return jsonify({
        'questions': [q.to_dict() for q in questions],
        'count': len(questions)
    }), 200


@questions_bp.route('/<int:question_id>', methods=['GET'])
@jwt_required()
def get_question(question_id):
    """Get single question by ID"""
    question = Question.query.get_or_404(question_id)
    return jsonify({'question': question.to_dict()}), 200


@questions_bp.route('/', methods=['POST'])
@jwt_required()
def create_question():
    """Create a new question"""
    data = request.get_json()
    user_id = get_jwt_identity()

    # Validate required fields
    required = ['text', 'question_type', 'blooms_level', 'difficulty', 'marks', 'subject_id']
    if not all(k in data for k in required):
        return jsonify({'error': f'Required fields: {required}'}), 400

    # Validate values
    if data['blooms_level'] not in VALID_BLOOMS:
        return jsonify({'error': f'blooms_level must be one of {VALID_BLOOMS}'}), 400

    if data['difficulty'] not in VALID_DIFFICULTY:
        return jsonify({'error': f'difficulty must be one of {VALID_DIFFICULTY}'}), 400

    if data['question_type'] not in VALID_TYPES:
        return jsonify({'error': f'question_type must be one of {VALID_TYPES}'}), 400

    # Check subject exists
    if not Subject.query.get(data['subject_id']):
        return jsonify({'error': 'Subject not found'}), 404

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
        created_by=int(user_id)
    )

    db.session.add(question)
    db.session.commit()

    return jsonify({
        'message': 'Question created successfully',
        'question': question.to_dict()
    }), 201


@questions_bp.route('/<int:question_id>', methods=['PUT'])
@jwt_required()
def update_question(question_id):
    """Update an existing question"""
    question = Question.query.get_or_404(question_id)
    data = request.get_json()

    question.text = data.get('text', question.text)
    question.blooms_level = data.get('blooms_level', question.blooms_level)
    question.difficulty = data.get('difficulty', question.difficulty)
    question.marks = data.get('marks', question.marks)
    question.option_a = data.get('option_a', question.option_a)
    question.option_b = data.get('option_b', question.option_b)
    question.option_c = data.get('option_c', question.option_c)
    question.option_d = data.get('option_d', question.option_d)
    question.correct_answer = data.get('correct_answer', question.correct_answer)

    db.session.commit()

    return jsonify({
        'message': 'Question updated successfully',
        'question': question.to_dict()
    }), 200


@questions_bp.route('/<int:question_id>', methods=['DELETE'])
@jwt_required()
def delete_question(question_id):
    """Delete a question"""
    question = Question.query.get_or_404(question_id)

    db.session.delete(question)
    db.session.commit()

    return jsonify({'message': 'Question deleted successfully'}), 200