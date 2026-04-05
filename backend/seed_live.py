import os, sys

os.environ["DATABASE_URL"] = "postgresql://postgres.dgeivjsswkozeyyehong:akashchidori@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
sys.path.insert(0, os.path.abspath("backend"))

from app import create_app, db
from app.models.subject import Subject
from app.models.question import Question
from seed_questions import QUESTIONS

def extract_and_exec():
    with open("backend/seed_100.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    func_lines = []
    in_func = False
    for line in lines:
        if line.strip() == "def get_subject_data(name):":
            in_func = True
        if in_func:
            func_lines.append(line[4:] if line.startswith('    ') else line)
            if line.strip() == "return []":
                break
                
    func_code = "".join(func_lines)
    local_vars = {}
    exec(func_code, globals(), local_vars)
    return local_vars['get_subject_data']

get_subject_data = extract_and_exec()

def seed_remaining():
    app = create_app()
    with app.app_context():
        inserted = 0
        
        # 1. From seed_100.py (232 questions)
        subjects = {s.name: s.id for s in Subject.query.all()}
        for subj_name, s_id in subjects.items():
            q_list = get_subject_data(subj_name)
            if not q_list: continue
            for q in q_list:
                text, q_type, blooms, diff, marks, opts, ans = q
                oa = ob = oc = od = None
                if opts: oa, ob, oc, od = opts
                def trunc(val):
                    return val[:255] if val and isinstance(val, str) else val

                new_q = Question(
                    text=text,
                    question_type=q_type,
                    blooms_level=blooms,
                    difficulty=diff,
                    marks=marks,
                    option_a=trunc(oa),
                    option_b=trunc(ob),
                    option_c=trunc(oc),
                    option_d=trunc(od),
                    correct_answer=trunc(ans),
                    subject_id=s_id,
                    created_by=1
                )
                db.session.add(new_q)
                inserted += 1
                
        # 2. From seed_questions.py (60 questions for Subject 1)
        # Getting Subject 1 (Theory of Computation or the first one)
        s_id = 1
        for level, qlist in QUESTIONS.items():
            for q in qlist:
                def trunc(val):
                    return val[:255] if val and isinstance(val, str) else val

                new_q = Question(
                    text=q["text"],
                    question_type=q["q_type"],
                    blooms_level=level,
                    difficulty=q["difficulty"],
                    marks=q["marks"],
                    option_a=trunc(q.get("oa")),
                    option_b=trunc(q.get("ob")),
                    option_c=trunc(q.get("oc")),
                    option_d=trunc(q.get("od")),
                    correct_answer=trunc(q.get("ca")),
                    subject_id=s_id,
                    created_by=1
                )
                db.session.add(new_q)
                inserted += 1
                
        db.session.commit()
        print(f"✅ Successfully appended {inserted} MORE questions to Live Supabase!")

if __name__ == '__main__':
    seed_remaining()
