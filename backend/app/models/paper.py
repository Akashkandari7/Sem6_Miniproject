from app.extensions import db
from datetime import datetime


# Association table - links papers to questions (many-to-many)
paper_questions = db.Table('paper_questions',
    db.Column('paper_id', db.Integer, db.ForeignKey('papers.id'), primary_key=True),
    db.Column('question_id', db.Integer, db.ForeignKey('questions.id'), primary_key=True),
    db.Column('order', db.Integer, nullable=False, default=0)  # question order in paper
)


class Paper(db.Model):
    __tablename__ = 'papers'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    total_marks = db.Column(db.Integer, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)  # exam duration
    
    # Configuration snapshot (what settings were used to generate)
    config = db.Column(db.JSON, nullable=False)
    # e.g. {
    #   "blooms_distribution": {"remember": 20, "understand": 30, "apply": 50},
    #   "difficulty_distribution": {"easy": 30, "medium": 50, "hard": 20}
    # }

    # Status
    status = db.Column(db.String(20), default='draft')  # 'draft', 'final'

    # Foreign keys
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Many-to-many relationship with questions
    questions = db.relationship('Question', secondary=paper_questions,
                                backref='papers', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'total_marks': self.total_marks,
            'duration_minutes': self.duration_minutes,
            'config': self.config,
            'status': self.status,
            'subject_id': self.subject_id,
            'created_by': self.created_by,
            'question_count': len(self.questions),
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Paper {self.id}: {self.title}>'