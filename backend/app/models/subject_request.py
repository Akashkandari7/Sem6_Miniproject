from app.extensions import db
from datetime import datetime, timezone


class SubjectRequest(db.Model):
    __tablename__ = 'subject_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    
    # Optional metadata
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = db.relationship('User', backref=db.backref('subject_requests', lazy=True))
    subject = db.relationship('Subject', backref=db.backref('requests', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name,
            'subject_code': self.subject.code,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f'<SubjectRequest {self.id}: User {self.user_id} -> Subject {self.subject_id}>'
