from app.models.question import Question


def generate_paper(subject_id, total_marks, config):
    """
    Smart question selection algorithm.
    
    Selects questions based on:
    - Bloom's taxonomy distribution
    - Difficulty distribution
    - Marks target
    - Usage count (least used questions preferred)
    """

    blooms_dist = config.get('blooms_distribution', {})
    difficulty_dist = config.get('difficulty_distribution', {})
    question_type = config.get('question_type', 'mixed')

    selected_questions = []
    used_ids = set()
    marks_allocated = 0

    # Step 1: Select questions by Bloom's distribution
    # blooms_dist = {"remember": 20, "apply": 50, ...} (values are % of total marks)
    for blooms_level, percentage in blooms_dist.items():

        target_marks = round((percentage / 100) * total_marks)
        level_marks = 0

        # Build query for this bloom's level
        query = Question.query.filter_by(
            subject_id=subject_id,
            blooms_level=blooms_level
        )

        # Filter by question type if not mixed
        if question_type != 'mixed':
            query = query.filter_by(question_type=question_type)

        # Prefer least used questions (avoids repetition)
        questions = query.order_by(Question.times_used.asc()).all()

        # Step 2: Apply difficulty distribution within each bloom's level
        for difficulty, diff_percentage in difficulty_dist.items():
            diff_target = round((diff_percentage / 100) * target_marks)
            diff_marks = 0

            diff_questions = [
                q for q in questions
                if q.difficulty == difficulty and q.id not in used_ids
            ]

            for q in diff_questions:
                if diff_marks + q.marks <= diff_target:
                    selected_questions.append(q)
                    used_ids.add(q.id)
                    diff_marks += q.marks
                    level_marks += q.marks
                    marks_allocated += q.marks

    # Step 3: Validate we got enough questions
    if not selected_questions:
        return {
            'success': False,
            'message': 'Not enough questions in the bank. Please add more questions first.'
        }

    # Step 4: Sort questions — easy to hard, then by bloom's level
    blooms_order = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
    difficulty_order = ['easy', 'medium', 'hard']

    selected_questions.sort(key=lambda q: (
        blooms_order.index(q.blooms_level),
        difficulty_order.index(q.difficulty)
    ))

    return {
        'success': True,
        'questions': selected_questions,
        'total_marks_allocated': marks_allocated,
        'total_questions': len(selected_questions)
    }