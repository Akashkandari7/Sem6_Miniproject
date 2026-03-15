from app.models.question import Question


def generate_paper(subject_id, total_marks, config):
    """
    Smart question selection algorithm with three modes:
    1. Custom Mode: Pick exact count of questions per mark value.
    2. Smart Mode Pass 1: Select questions respecting Bloom's and Difficulty.
    3. Smart Mode Pass 2: Backfill remaining marks from the subject pool.
    """

    custom_dist = config.get('custom_distribution') # e.g., {1: 20, 3: 10, 5: 10, 10: 10}
    max_mcqs = config.get('max_mcqs') # e.g., 10
    
    selected_questions = []
    used_ids = set()
    marks_allocated = 0
    mcq_count = 0

    # MODE 1: Custom Explicit Distribution
    if custom_dist:
        for marks, count in custom_dist.items():
            if count <= 0: continue
            
            # Enforce MCQ limit in manual mode
            actual_count = count
            if int(marks) == 1 and max_mcqs is not None:
                if count > max_mcqs:
                    return {
                        'success': False,
                        'message': f'Manual structure exceeds MCQ limit: {count} requested, but max is {max_mcqs}.'
                    }
            
            # Query pool for this mark value
            query = Question.query.filter_by(subject_id=subject_id, marks=int(marks))
            # Prefer least used
            pool = query.order_by(Question.times_used.asc()).limit(actual_count).all()
            
            for q in pool:
                selected_questions.append(q)
                used_ids.add(q.id)
                marks_allocated += q.marks
                if q.marks == 1:
                    mcq_count += 1
                
        # If we successfully allocated marks (doesn't have to be perfect if pool exhausted)
        # We skip Pass 1 & 2 if custom distribution was intended to be the full definition
        pass
    else:
        # MODE 2: Automatic Smart Distribution
        blooms_dist = config.get('blooms_distribution', {})
        difficulty_dist = config.get('difficulty_distribution', {})
        question_type = config.get('question_type', 'mixed')

        # Pass 1: Strict distribution-based selection
        for blooms_level, percentage in blooms_dist.items():
            target_marks_for_bloom = round((percentage / 100) * total_marks)
            bloom_marks_allocated = 0

            query = Question.query.filter_by(subject_id=subject_id, blooms_level=blooms_level)
            if question_type != 'mixed':
                query = query.filter_by(question_type=question_type)
            
            bloom_pool = query.order_by(Question.times_used.asc()).all()

            for difficulty, diff_percentage in difficulty_dist.items():
                target_for_bucket = round((diff_percentage / 100) * target_marks_for_bloom)
                bucket_marks = 0

                bucket_pool = [q for q in bloom_pool if q.difficulty == difficulty and q.id not in used_ids]

                for q in bucket_pool:
                    # Check MCQ limit for 1-mark questions
                    if q.marks == 1 and max_mcqs is not None and mcq_count >= max_mcqs:
                        continue
                        
                    if marks_allocated + q.marks <= total_marks and bucket_marks + q.marks <= target_for_bucket:
                        selected_questions.append(q)
                        used_ids.add(q.id)
                        bucket_marks += q.marks
                        bloom_marks_allocated += q.marks
                        marks_allocated += q.marks
                        if q.marks == 1:
                            mcq_count += 1

        # Pass 2: Backfill Pass (if we are under total_marks)
        if marks_allocated < total_marks:
            remaining_pool = Question.query.filter_by(subject_id=subject_id)\
                .filter(~Question.id.in_(used_ids))\
                .order_by(Question.times_used.asc(), Question.marks.desc()).all()

            if question_type != 'mixed':
                remaining_pool = [q for q in remaining_pool if q.question_type == question_type]

            for q in remaining_pool:
                # Check MCQ limit for 1-mark questions
                if q.marks == 1 and max_mcqs is not None and mcq_count >= max_mcqs:
                    continue
                    
                if marks_allocated + q.marks <= total_marks:
                    selected_questions.append(q)
                    used_ids.add(q.id)
                    marks_allocated += q.marks
                    if q.marks == 1:
                        mcq_count += 1

    # Finalization
    if not selected_questions:
        return {
            'success': False,
            'message': 'Not enough questions in the bank matching your criteria.'
        }

    # Sort questions — easy to hard, then by bloom's level
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