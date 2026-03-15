from app.models.question import Question


def generate_paper(subject_id, total_marks, config):
    """
    Smart question selection algorithm with two passes.
    
    1. Strict Pass: Select questions respecting Bloom's and Difficulty distributions.
    2. Backfill Pass: Fill remaining marks by picking from the subject pool.
    """

    blooms_dist = config.get('blooms_distribution', {})
    difficulty_dist = config.get('difficulty_distribution', {})
    question_type = config.get('question_type', 'mixed')

    selected_questions = []
    used_ids = set()
    marks_allocated = 0

    # Pass 1: Strict distribution-based selection
    for blooms_level, percentage in blooms_dist.items():
        # Calculate marks target for this Bloom's level
        target_marks_for_bloom = round((percentage / 100) * total_marks)
        bloom_marks_allocated = 0

        # Query pool for this Bloom's level
        query = Question.query.filter_by(subject_id=subject_id, blooms_level=blooms_level)
        if question_type != 'mixed':
            query = query.filter_by(question_type=question_type)
        
        # Prefer least used
        bloom_pool = query.order_by(Question.times_used.asc()).all()

        # Sub-distribution by difficulty within this Bloom's level
        for difficulty, diff_percentage in difficulty_dist.items():
            # Target for this specific (Bloom, Difficulty) bucket
            target_for_bucket = round((diff_percentage / 100) * target_marks_for_bloom)
            bucket_marks = 0

            bucket_pool = [q for q in bloom_pool if q.difficulty == difficulty and q.id not in used_ids]

            for q in bucket_pool:
                # If adding this question keeps us within bucket limit (with some flexibility for large mark questions)
                if marks_allocated + q.marks <= total_marks and bucket_marks + q.marks <= target_for_bucket:
                    selected_questions.append(q)
                    used_ids.add(q.id)
                    bucket_marks += q.marks
                    bloom_marks_allocated += q.marks
                    marks_allocated += q.marks

    # Pass 2: Backfill Pass (if we are under total_marks)
    if marks_allocated < total_marks:
        # Get all remaining questions for this subject, sorted by usage and marks
        remaining_pool = Question.query.filter_by(subject_id=subject_id)\
            .filter(~Question.id.in_(used_ids))\
            .order_by(Question.times_used.asc(), Question.marks.desc()).all()

        if question_type != 'mixed':
            remaining_pool = [q for q in remaining_pool if q.question_type == question_type]

        for q in remaining_pool:
            if marks_allocated + q.marks <= total_marks:
                selected_questions.append(q)
                used_ids.add(q.id)
                marks_allocated += q.marks
            
            if marks_allocated == total_marks:
                break

    # Step 3: Validate we got enough questions
    if not selected_questions:
        return {
            'success': False,
            'message': 'Not enough questions in the bank matching your criteria.'
        }

    # Step 4: Sort questions — easy to hard, then by bloom's level
    blooms_order = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
    difficulty_order = ['easy', 'medium', 'hard']

    selected_questions.sort(key=lambda q: (
        blooms_order.index(q.blooms_level) if q.blooms_level in blooms_order else 99,
        difficulty_order.index(q.difficulty) if q.difficulty in difficulty_order else 99
    ))

    return {
        'success': True,
        'questions': selected_questions,
        'total_marks_allocated': marks_allocated,
        'total_questions': len(selected_questions)
    }