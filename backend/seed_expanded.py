import os
import sys
from datetime import datetime

# Add the parent directory to sys.path to import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.subject import Subject
from app.models.question import Question

def seed_expanded():
    app = create_app()
    with app.app_context():
        # Get all subjects
        subjects = Subject.query.all()
        if not subjects:
            print("No subjects found. Please seed subjects first.")
            return

        # Target distribution per subject: 20x1, 10x3, 10x5, 10x10
        target = {1: 20, 3: 10, 5: 10, 10: 10}
        
        blooms = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
        difficulties = ['easy', 'medium', 'hard']
        
        new_questions_count = 0
        
        for sub in subjects:
            print(f"Checking distribution for {sub.name}...")
            
            for marks, total_needed in target.items():
                # Count current questions for this mark and subject
                current_count = Question.query.filter_by(subject_id=sub.id, marks=marks).count()
                to_add = total_needed - current_count
                
                if to_add > 0:
                    print(f"  Adding {to_add} questions of {marks} marks...")
                    for i in range(to_add):
                        q_type = 'mcq' if marks == 1 else ('short' if marks == 3 else 'long')
                        
                        # Generate some generic but relevant-sounding text for the subject
                        texts = {
                            1: [
                                f"What is the primary function of {sub.name} in modern computing?",
                                f"In {sub.name}, which component handles core logic?",
                                f"True or False: {sub.name} principles are obsolete.",
                                f"Which standard defines {sub.name} protocols?",
                                f"Define the base unit of measurement in {sub.name}.",
                                f"Identify the key inventor of {sub.name} theories.",
                                f"What is the time complexity of the basic {sub.name} algorithm?",
                                f"Which layer of the OSI model does {sub.name} primarily target?",
                                f"What is the hexadecimal representation of the default {sub.name} port?",
                                f"Which company first commercialized {sub.name} technology?"
                            ],
                            3: [], # Should already have 10
                            5: [
                                f"Explain the internal mechanism of {sub.name} with a diagram.",
                                f"Compare and contrast two major approaches in {sub.name}.",
                                f"Describe the evolution of {sub.name} over the last decade.",
                                f"How does {sub.name} impact system performance and scalability?",
                                f"Explain the security implications of {sub.name} in cloud environments.",
                                f"Discuss the integration of {sub.name} with AI and Machine Learning."
                            ],
                            10: [
                                f"Critically analyze the performance of various {sub.name} algorithms and propose an optimization strategy.",
                                f"Design a comprehensive framework for implementing {sub.name} in a large-scale enterprise environment.",
                                f"Evaluate the ethical considerations and regulatory challenges associated with {sub.name}.",
                                f"Perform a deep-dive into the mathematical foundations of {sub.name} and prove its efficiency.",
                                f"Synthesize a new architectural pattern for {sub.name} that addresses modern low-latency requirements.",
                                f"Discuss the role of {sub.name} in the future of quantum computing and distributed systems.",
                                f"Create a detailed case study on the failure of a major {sub.name} implementation and suggest fixes."
                            ]
                        }
                        
                        text_list = texts.get(marks, ["Standard knowledge assessment question."])
                        text = text_list[i % len(text_list)] + f" (Ref: E{sub.id}-{marks}-{i})"
                        
                        q = Question(
                            text=text,
                            question_type=q_type,
                            blooms_level=blooms[i % len(blooms)],
                            difficulty=difficulties[i % len(difficulties)],
                            marks=marks,
                            subject_id=sub.id,
                            created_by=2 # Using admin user id from previous logs
                        )
                        
                        # Add options for MCQ
                        if q_type == 'mcq':
                            q.option_a = "Option A"
                            q.option_b = "Option B"
                            q.option_c = "Option C"
                            q.option_d = "Option D"
                            q.correct_answer = "Option A"
                            
                        db.session.add(q)
                        new_questions_count += 1
        
        db.session.commit()
        print(f"Seeding complete! Added {new_questions_count} new questions.")

if __name__ == '__main__':
    seed_expanded()
