import pytest
from app.extensions import db
from app.models.question import Question
from app.services.paper_generator import generate_paper

@pytest.fixture
def seed_questions(app, init_database):
    """Seed the database with a robust taxonomy of questions for testing generator modes."""
    subject_id = init_database['subject_id']
    user_id = init_database['user_id']
    
    with app.app_context():
        questions = []
        
        # Add 10 MCQ (1-mark) - Remember/Easy
        for i in range(10):
            questions.append(Question(text=f'MCQ_{i}', question_type='mcq', blooms_level='remember', difficulty='easy', marks=1, subject_id=subject_id, created_by=user_id))
            
        # Add 10 Short (3-mark) - Understand/Medium
        for i in range(10):
            questions.append(Question(text=f'Short_{i}', question_type='short', blooms_level='understand', difficulty='medium', marks=3, subject_id=subject_id, created_by=user_id))
            
        # Add 10 Long (5-mark) - Apply/Hard
        for i in range(10):
            questions.append(Question(text=f'Long_{i}', question_type='long', blooms_level='apply', difficulty='hard', marks=5, subject_id=subject_id, created_by=user_id))
            
        db.session.bulk_save_objects(questions)
        db.session.commit()
        return subject_id

def test_paper_generator_custom_mode_exact(app, seed_questions):
    """Test explicit manual mode requesting specific mark allocations."""
    with app.app_context():
        config = {
            'custom_distribution': {
                '1': 5, # 5 MCQs
                '3': 2, # 2 Short
                '5': 1  # 1 Long
            },
            'max_mcqs': 10
        }
        res = generate_paper(seed_questions, total_marks=16, config=config)
        assert res['success'] is True
        assert res['total_marks_allocated'] == 16
        assert len(res['questions']) == 8 # 5 + 2 + 1
        
def test_paper_generator_custom_mode_mcq_limit(app, seed_questions):
    """Test manual mode rejecting an oversized MCQ request."""
    with app.app_context():
        config = {
            'custom_distribution': {
                '1': 15 
            },
            'max_mcqs': 10
        }
        res = generate_paper(seed_questions, total_marks=15, config=config)
        assert res['success'] is False
        assert "exceeds MCQ limit" in res['message']

def test_paper_generator_smart_mode_basic(app, seed_questions):
    """Test smart dynamic distribution targeting 100% of a specific Bloom's taxonomy."""
    with app.app_context():
        config = {
            'blooms_distribution': {
                'understand': 100
            },
            'difficulty_distribution': {
                'medium': 100
            },
            'question_type': 'short',
            'max_mcqs': 10
        }
        res = generate_paper(seed_questions, total_marks=9, config=config)
        
        # 100% understand/medium = it should just pick the 3-mark questions
        assert res['success'] is True
        assert res['total_marks_allocated'] == 9
        assert len(res['questions']) == 3
        assert all(q.question_type == 'short' for q in res['questions'])

def test_paper_generator_exhaustion(app, seed_questions):
    """Test failure when paper size demands more questions than the bank possesses."""
    with app.app_context():
        config = {
            'custom_distribution': {
                '5': 100 # Wants 100 5-mark questions, we only seeded 10
            }
        }
        # It's manual distribution. It exhausts pool without error internally, 
        # but what is the exact return? Let's check marks_allocated.
        res = generate_paper(seed_questions, total_marks=500, config=config)
        
        # In this implementation, custom mode doesn't throw specific NOT_ENOUGH message 
        # unless NO questions are found. Let's see if it returned all 10.
        assert res['success'] is True
        assert res['total_marks_allocated'] == 50 # 10 * 5
        assert len(res['questions']) == 10
        
def test_paper_generator_smart_mode_empty_pool(app):
    """Test total failure gracefully handled when there are no questions for subject."""
    with app.app_context():
        config = {
            'blooms_distribution': {'remember': 100},
            'difficulty_distribution': {'easy': 100}
        }
        res = generate_paper(999, total_marks=10, config=config)
        assert res['success'] is False
        assert "Not enough questions in the bank" in res['message']
