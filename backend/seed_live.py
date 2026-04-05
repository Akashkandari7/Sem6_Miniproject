import os
import re
import sys

# Force the Supabase URL
os.environ["DATABASE_URL"] = "postgresql://postgres.dgeivjsswkozeyyehong:akashchidori@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

# Also set APP_DIR to ensure it correctly resolves module paths if executed outside backend
sys.path.insert(0, os.path.abspath("backend"))

from app import create_app, db
from app.models.subject import Subject
from app.models.question import Question

def seed_live():
    app = create_app()
    
    # Extract all_data from backend/seed_bulk.py
    with open("backend/seed_bulk.py", "r", encoding="utf-8") as f:
        code = f.read()
        dict_match = re.search(r'all_data = (\{.*?\n    \})\n\n    try', code, re.DOTALL)
        if dict_match:
            all_data = eval(dict_match.group(1))
        else:
            print("Failed to parse dictionary from seed_bulk.py")
            return

    with app.app_context():
        # Clean current live questions (if any)
        Question.query.delete()
        
        # Get mapping of live subject names to IDs
        subjects = {s.name: s.id for s in Subject.query.all()}
        
        inserted = 0
        for subj_name, questions in all_data.items():
            s_id = subjects.get(subj_name)
            if not s_id:
                continue
                
            for q in questions:
                text, q_type, blooms, diff, marks, opts, ans = q
                oa = ob = oc = od = None
                if opts:
                    oa, ob, oc, od = opts
                
                new_q = Question(
                    text=text,
                    question_type=q_type,
                    blooms_level=blooms,
                    difficulty=diff,
                    marks=marks,
                    option_a=oa,
                    option_b=ob,
                    option_c=oc,
                    option_d=od,
                    correct_answer=ans,
                    subject_id=s_id,
                    created_by=1  # Admin user ID is 1
                )
                db.session.add(new_q)
                inserted += 1
                
        db.session.commit()
        print(f"✅ Successfully seeded {inserted} questions to Live Supabase!")

if __name__ == '__main__':
    seed_live()
