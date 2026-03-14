
import sqlite3
from datetime import datetime

DB_PATH = "backend/instance/qpgen.db"
CREATED_BY = 1 # Assuming admin user id

def insert_question(cur, subject_id, text, q_type, blooms, difficulty, marks, options=None, correct_answer=None):
    now = datetime.utcnow().isoformat()
    oa = ob = oc = od = None
    if options:
        oa, ob, oc, od = options
    
    cur.execute(
        """INSERT INTO questions 
        (text, question_type, blooms_level, difficulty, marks, option_a, option_b, option_c, option_d, correct_answer, subject_id, created_by, created_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (text, q_type, blooms, difficulty, marks, oa, ob, oc, od, correct_answer, subject_id, CREATED_BY, now)
    )

def seed():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Get subject map
    cur.execute("SELECT id, name FROM subjects")
    subjects = {name: id for id, name in cur.fetchall()}

    # Data to seed (Sample questions for each subject)
    # Format: (Subject Name, questions list)
    data = [
        ("Theory of Computation", [
            ("Which of the following machines can recognize Context Free Languages?", "mcq", "remember", "easy", 1, ("Finite Automata", "Pushdown Automata", "Turing Machine", "Linear Bounded Automata"), "Pushdown Automata"),
            ("Define Chomsky Normal Form (CNF) for Context-Free Grammars.", "short", "understand", "medium", 3, None, "A CFG is in CNF if all its production rules are of the form A -> BC or A -> a."),
        ]),
        ("DBMS", [
            ("Which normal form eliminates partial functional dependencies?", "mcq", "remember", "easy", 1, ("1NF", "2NF", "3NF", "BCNF"), "2NF"),
            ("Explain the ACID properties in database transactions.", "long", "understand", "medium", 5, None, "Atomicity, Consistency, Isolation, and Durability ensure reliable transaction processing."),
        ]),
        ("Software Engineering", [
            ("What is the primary goal of the Waterall model?", "mcq", "remember", "easy", 1, ("Iterative development", "Linear sequential development", "Rapid prototyping", "Customer feedback"), "Linear sequential development"),
            ("Describe the difference between black-box and white-box testing.", "short", "analyze", "medium", 4, None, "Black-box tests functionality without knowing internal code; White-box tests internal structure and logic."),
        ]),
        ("Computer Networks", [
            ("Which layer of the OSI model is responsible for routing?", "mcq", "remember", "easy", 1, ("Physical", "Data Link", "Network", "Transport"), "Network"),
            ("How does the Three-Way Handshake work in TCP?", "short", "understand", "medium", 3, None, "It uses SYN, SYN-ACK, and ACK packets to establish a connection."),
        ]),
        ("Operating System", [
            ("What is a deadlock in an operating system?", "short", "understand", "easy", 2, None, "A situation where a set of processes are blocked because each is holding a resource and waiting for another."),
            ("Explain the concept of Virtual Memory.", "long", "understand", "medium", 5, None, "A memory management technique that provides an 'idealized' abstraction of the storage resources actually available."),
        ]),
        ("Cyber Security", [
            ("What does the 'A' in the CIA triad stand for?", "mcq", "remember", "easy", 1, ("Authentication", "Accounting", "Availability", "Authorization"), "Availability"),
            ("Explain the difference between Symmetrical and Asymmetrical encryption.", "short", "analyze", "medium", 4, None, "Symmetric uses one key for both; Asymmetric uses public and private key pairs."),
        ]),
        ("COA", [
            ("What is the function of the Program Counter (PC)?", "mcq", "remember", "easy", 1, ("Stores data", "Stores address of next instruction", "Performs arithmetic", "Controls I/O"), "Stores address of next instruction"),
            ("Describe the basic instruction cycle of a computer.", "short", "understand", "medium", 3, None, "Fetch, Decode, and Execute."),
        ]),
        ("OOPs", [
            ("Which concept allows a class to inherit properties from another class?", "mcq", "remember", "easy", 1, ("Encapsulation", "Polymorphism", "Inheritance", "Abstraction"), "Inheritance"),
            ("Explain the concept of Method Overloading with an example.", "short", "apply", "medium", 3, None, "Defining multiple methods with the same name but different parameters."),
        ])
    ]

    try:
        for subj_name, questions in data:
            s_id = subjects.get(subj_name)
            if s_id:
                for q in questions:
                    insert_question(cur, s_id, *q)
        con.commit()
        print("Successfully seeded initial questions for all subjects.")
    except Exception as e:
        con.rollback()
        print(f"Error: {e}")
    finally:
        con.close()

if __name__ == "__main__":
    seed()
