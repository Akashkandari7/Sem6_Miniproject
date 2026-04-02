from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.subject import Subject
from app.authorization import require_permission

subjects_bp = Blueprint('subjects', __name__)


@subjects_bp.route('/', methods=['GET'])
@require_permission('subjects.read')
def get_subjects():
    """Get all subjects."""
    subjects = Subject.query.all()
    return jsonify({
        'subjects': [s.to_dict() for s in subjects],
        'count': len(subjects),
    }), 200


@subjects_bp.route('/<int:subject_id>', methods=['GET'])
@require_permission('subjects.read')
def get_subject(subject_id):
    """Get a single subject by ID."""
    subject = db.get_or_404(Subject, subject_id)
    return jsonify({'subject': subject.to_dict()}), 200


@subjects_bp.route('/', methods=['POST'])
@require_permission('subjects.create')
def create_subject():
    """Create a new subject."""
    data = request.get_json()

    if not all(k in data for k in ['name', 'code']):
        return jsonify({'error': 'name and code are required'}), 400

    if Subject.query.filter_by(code=data['code'].upper()).first():
        return jsonify({'error': 'Subject code already exists'}), 409

    subject = Subject(
        name=data['name'],
        code=data['code'].upper(),
        description=data.get('description', ''),
    )

    db.session.add(subject)
    db.session.commit()

    return jsonify({
        'message': 'Subject created successfully',
        'subject': subject.to_dict(),
    }), 201


@subjects_bp.route('/<int:subject_id>', methods=['PUT'])
@require_permission('subjects.update')
def update_subject(subject_id):
    """Update an existing subject."""
    subject = db.get_or_404(Subject, subject_id)
    data = request.get_json()

    subject.name        = data.get('name',        subject.name)
    subject.description = data.get('description', subject.description)

    db.session.commit()

    return jsonify({
        'message': 'Subject updated successfully',
        'subject': subject.to_dict(),
    }), 200


@subjects_bp.route('/<int:subject_id>', methods=['DELETE'])
@require_permission('subjects.delete')
def delete_subject(subject_id):
    """Delete a subject."""
    subject = db.get_or_404(Subject, subject_id)

    db.session.delete(subject)
    db.session.commit()

    return jsonify({'message': 'Subject deleted successfully'}), 200
