from app.extensions import db
from datetime import datetime


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # 'mcq', 'short', 'long'
    
    # Bloom's Taxonomy level
    blooms_level = db.Column(db.String(20), nullable=False)  # 'remember', 'understand', 
                                                              # 'apply', 'analyze', 
                                                              # 'evaluate', 'create'
    
    difficulty = db.Column(db.String(10), nullable=False)    # 'easy', 'medium', 'hard'
    marks = db.Column(db.Integer, nullable=False, default=1)
    
    # For MCQ questions
    option_a = db.Column(db.String(255), nullable=True)
    option_b = db.Column(db.String(255), nullable=True)
    option_c = db.Column(db.String(255), nullable=True)
    option_d = db.Column(db.String(255), nullable=True)
    correct_answer = db.Column(db.String(255), nullable=True)
    
    # Metadata
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    times_used = db.Column(db.Integer, default=0)  # tracks usage for smart selection
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Bloom's levels as a constant — single source of truth
    BLOOMS_LEVELS = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
    DIFFICULTY_LEVELS = ['easy', 'medium', 'hard']
    QUESTION_TYPES = ['mcq', 'short', 'long']

    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'question_type': self.question_type,
            'blooms_level': self.blooms_level,
            'difficulty': self.difficulty,
            'marks': self.marks,
            'options': {
                'a': self.option_a,
                'b': self.option_b,
                'c': self.option_c,
                'd': self.option_d,
            } if self.question_type == 'mcq' else None,
            'correct_answer': self.correct_answer,
            'subject_id': self.subject_id,
            'times_used': self.times_used,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Question {self.id}: {self.blooms_level} | {self.difficulty}>'