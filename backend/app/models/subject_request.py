from app.extensions import db
from datetime import datetime, timezone


class SubjectRequest(db.Model):
    __tablename__ = 'subject_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # 'access' = request access to existing subject, 'new_subject' = propose a brand-new subject
    request_type = db.Column(db.String(20), default='access')

    # For 'access' requests — links to an existing subject
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=True)

    # For 'new_subject' requests — proposed subject details
    subject_name = db.Column(db.String(100), nullable=True)
    subject_code = db.Column(db.String(20), nullable=True)
    subject_description = db.Column(db.Text, nullable=True)
    topics = db.Column(db.Text, nullable=True)  # Comma-separated list of topics

    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'

    # Optional metadata
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = db.relationship('User', backref=db.backref('subject_requests', lazy=True))
    subject = db.relationship('Subject', backref=db.backref('requests', lazy=True))

    def to_dict(self):
        d = {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username,
            'request_type': self.request_type or 'access',
            'status': self.status,
            'admin_notes': self.admin_notes,
            'topics': self.topics,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

        if self.request_type == 'new_subject':
            d['subject_name'] = self.subject_name
            d['subject_code'] = self.subject_code
            d['subject_description'] = self.subject_description
        else:
            d['subject_id'] = self.subject_id
            d['subject_name'] = self.subject.name if self.subject else None
            d['subject_code'] = self.subject.code if self.subject else None

        return d

    def __repr__(self):
        return f'<SubjectRequest {self.id}: User {self.user_id} -> {self.request_type}>'
