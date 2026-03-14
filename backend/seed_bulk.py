
import sqlite3
import os
from datetime import datetime

DB_PATH = "backend/instance/qpgen.db"
CREATED_BY = 1 # Admin

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

    print("Clearing existing questions for a clean seed...")
    cur.execute("DELETE FROM questions;")
    try:
        cur.execute("DELETE FROM sqlite_sequence WHERE name='questions';")
    except sqlite3.OperationalError:
        pass

    cur.execute("SELECT id, name FROM subjects")
    subjects = {name: id for id, name in cur.fetchall()}

    # Data Dictionary for all 8 subjects
    all_data = {
        "Theory of Computation": [
            ("Which of the following machines can recognize Context Free Languages?", "mcq", "remember", "easy", 1, ("Finite Automata", "Pushdown Automata", "Turing Machine", "Linear Bounded Automata"), "Pushdown Automata"),
            ("Regular expressions can represent which type of languages?", "mcq", "remember", "easy", 1, ("Recursive", "Context Free", "Regular", "Turing-recognizable"), "Regular"),
            ("Which machine has the highest computational power?", "mcq", "remember", "easy", 1, ("NFA", "PDA", "Turing Machine", "DFA"), "Turing Machine"),
            ("A language is regular if and only if it is accepted by a:", "mcq", "understand", "easy", 1, ("Stack machine", "Finite automaton", "Turing machine", "Universal machine"), "Finite automaton"),
            ("Which of the following is NOT a closure property of regular languages?", "mcq", "remember", "medium", 1, ("Union", "Intersection", "Complement", "Subset"), "Subset"),
            ("Define the Pumping Lemma for regular languages.", "short", "understand", "medium", 3, None, "A tool used to prove that a language is not regular."),
            ("Distinguish between a Deterministic Finite Automaton (DFA) and a Non-deterministic Finite Automaton (NFA).", "short", "analyze", "medium", 3, None, "DFA has exactly one transition per input; NFA can have zero, one, or multiple."),
            ("What is the difference between a Mealy machine and a Moore machine?", "short", "analyze", "medium", 3, None, "Mealy output depends on state and input; Moore output depends only on state."),
            ("Explain the concept of an ambiguous grammar.", "short", "understand", "medium", 3, None, "A grammar is ambiguous if there exists more than one parse tree for a single string."),
            ("Define a recursive language.", "short", "remember", "medium", 3, None, "A language for which there is a Turing machine that halts for all inputs."),
            ("Construct a DFA that accepts strings ending with '01' over binary alphabet.", "long", "apply", "medium", 5, None, "Description of states and transitions."),
            ("Explain the Chomsky Hierarchy of languages and their corresponding machines.", "long", "understand", "hard", 5, None, "Type 0 (Turing), Type 1 (LBA), Type 2 (PDA), Type 3 (FA)."),
            ("Critically evaluate the Halting Problem and explain why it is undecidable.", "long", "evaluate", "hard", 10, None, "Formal proof and implications on computation."),
            ("Design a Turing Machine to perform binary addition of two numbers provided on the tape.", "long", "create", "hard", 10, None, "State transitions and tape movement logic.")
        ],
        "DBMS": [
            ("Which clause is used to filter results after grouping in SQL?", "mcq", "remember", "easy", 1, ("WHERE", "HAVING", "GROUP BY", "ORDER BY"), "HAVING"),
            ("Unique constraint allows multiple NULL values?", "mcq", "understand", "medium", 1, ("Yes", "No", "Only one", "Depends on SQL engine"), "Yes"),
            ("Which key uniquely identifies a record in another table?", "mcq", "remember", "easy", 1, ("Primary Key", "Foreign Key", "Candidate Key", "Super Key"), "Foreign Key"),
            ("ACID properties stand for Atomicity, Consistency, Isolation and:", "mcq", "remember", "easy", 1, ("Data", "Durability", "Dependencies", "Denormalization"), "Durability"),
            ("Data redundancy is eliminated using which process?", "mcq", "understand", "easy", 1, ("Backup", "Normalization", "Indexing", "Joins"), "Normalization"),
            ("Explain the concept of Functional Dependency in DBMS.", "short", "understand", "medium", 3, None, "Relationship between attributes where property of A determines property of B."),
            ("What is a deadlock and how can it be detected in transactions?", "short", "understand", "medium", 3, None, "Mutual waiting state; detected via Wait-for Graphs."),
            ("Describe the difference between 2NF and 3NF.", "short", "analyze", "medium", 3, None, "2NF removes partial dependency; 3NF removes transitive dependency."),
            ("Explain the concept of 'View' in SQL and its advantages.", "short", "understand", "medium", 3, None, "Virtual table; security and simplification of complex queries."),
            ("What are stored procedures and why are they used?", "short", "remember", "medium", 3, None, "Precompiled SQL code saved in database for reuse and efficiency."),
            ("Explain the indexing mechanism in B-Trees used by DBMS.", "long", "analyze", "hard", 5, None, "Hierarchical balancing and search logic."),
            ("Differentiate between Strong and Weak entity sets with an ER diagram example.", "long", "understand", "medium", 5, None, "Strong has PK; Weak depends on identifying owner."),
            ("Design a normalized database schema (up to 3NF) for a Hospital Management System.", "long", "create", "hard", 10, None, "Tables, PKs, FKs for Patients, Doctors, Appointments."),
            ("Evaluate the trade-offs between Relational Databases and NoSQL databases for a High-Volume Social Media app.", "long", "evaluate", "hard", 10, None, "Scalability vs ACID vs Schema flexibility.")
        ],
        "Software Engineering": [
            ("Which phase of SDLC involves fixing bugs after release?", "mcq", "remember", "easy", 1, ("Testing", "Deployment", "Maintenance", "Implementation"), "Maintenance"),
            ("Black-box testing is also known as:", "mcq", "remember", "easy", 1, ("Structural testing", "Logic testing", "Functional testing", "Glass-box testing"), "Functional testing"),
            ("Cohesion should ideally be:", "mcq", "understand", "medium", 1, ("Low", "High", "Loose", "Negative"), "High"),
            ("The Waterfall model is best for:", "mcq", "understand", "easy", 1, ("Dynamic projects", "Fixed requirement projects", "Large teams", "Startup apps"), "Fixed requirement projects"),
            ("What does 'UML' stand for?", "mcq", "remember", "easy", 1, ("Unique Model Link", "Unified Modeling Language", "User Method Level", "Universal Model List"), "Unified Modeling Language"),
            ("Explain the 'Agile' software development methodology.", "short", "understand", "medium", 3, None, "Iterative, incremental development based on client feedback."),
            ("What is the difference between Coupling and Cohesion?", "short", "analyze", "medium", 3, None, "Coupling: inter-module interaction; Cohesion: intra-module focus."),
            ("Define Software Reliability and how it's measured.", "short", "remember", "medium", 3, None, "Probability of failure-free operation; measured via MTBF."),
            ("What is the purpose of 'Regression Testing'?", "short", "understand", "medium", 3, None, "Ensuring that new code changes don't break existing functionality."),
            ("Explain the concept of Software Configuration Management.", "short", "understand", "medium", 3, None, "Tracking and controlling changes in the software development lifecycle."),
            ("Elaborate on the Spiral Model and its risk management focus.", "long", "understand", "medium", 5, None, "Iterative nature with explicit risk analysis phases."),
            ("Describe the McCall's Quality Model and its three pillars.", "long", "remember", "medium", 5, None, "Product Revision, Transition, and Operation."),
            ("Develop a comprehensive Software Requirement Specification (SRS) outline for a Student Portal.", "long", "create", "hard", 10, None, "Functional, non-functional, and technical requirements."),
            ("Evaluate the impact of choosing Microservices architecture over a Monolithic one for a banking system.", "long", "evaluate", "hard", 10, None, "Security, deployment complexity, data consistency challenges.")
        ],
        "Computer Networks": [
            ("Which layer is responsible for IP addressing?", "mcq", "remember", "easy", 1, ("Transport", "Network", "Data Link", "Session"), "Network"),
            ("HTTP works on which port by default?", "mcq", "remember", "easy", 1, ("21", "25", "80", "443"), "80"),
            ("A router operates at which OSI layer?", "mcq", "remember", "easy", 1, ("Layer 1", "Layer 2", "Layer 3", "Layer 4"), "Layer 3"),
            ("Which protocol is 'connectionless'?", "mcq", "understand", "easy", 1, ("TCP", "UDP", "FTP", "HTTP"), "UDP"),
            ("What is the size of an IPv4 address?", "mcq", "remember", "easy", 1, ("16 bits", "32 bits", "64 bits", "128 bits"), "32 bits"),
            ("Explain the functions of the Data Link Layer.", "short", "understand", "medium", 3, None, "Framing, error control, and flow control."),
            ("Describe the difference between Hub, Switch, and Router.", "short", "analyze", "medium", 3, None, "Hub broadcasts; Switch connects at L2; Router at L3."),
            ("What is DNS and why is it essential?", "short", "understand", "medium", 3, None, "Domain Name System; resolves hostnames to IP addresses."),
            ("Explain the concept of Subnetting.", "short", "apply", "medium", 3, None, "Dividing a large network into smaller manageable segments."),
            ("How does CSMA/CD handle collisions?", "short", "understand", "medium", 3, None, "Detects collision, stops transmission, and retries after random delay."),
            ("Explain the TCP 3-way handshake in detail.", "long", "understand", "medium", 5, None, "SYN, SYN-ACK, ACK packet exchange."),
            ("Describe the Distance Vector Routing algorithm (Bellman-Ford).", "long", "analyze", "hard", 5, None, "Routing table exchange and periodic updates."),
            ("Design a network topology for a college campus with 5 departments and a central server.", "long", "create", "hard", 10, None, "Star/Mesh topology with VLAN configurations."),
            ("Evaluate the security benefits and challenges of transitioning from IPv4 to IPv6.", "long", "evaluate", "hard", 10, None, "Address space, IPsec integration, and transition mechanisms.")
        ],
        "Operating System": [
            ("Which scheduler chooses processes from the ready queue?", "mcq", "remember", "easy", 1, ("Long-term", "Short-term", "Medium-term", "I/O scheduler"), "Short-term"),
            ("Context switching is the job of:", "mcq", "remember", "easy", 1, ("Interrupt", "Dispatcher", "Compiler", "Assembler"), "Dispatcher"),
            ("What is the main purpose of virtual memory?", "mcq", "understand", "easy", 1, ("Increase speed", "Run large programs", "Backup data", "Cache I/O"), "Run large programs"),
            ("Which algorithm is used for deadlock avoidance?", "mcq", "remember", "easy", 1, ("SJFS", "Banker's Algorithm", "Round Robin", "LRU"), "Banker's Algorithm"),
            ("A semaphore is basically an:", "mcq", "understand", "medium", 1, ("Integer variable", "Boolean flag", "System call", "Interrupt"), "Integer variable"),
            ("What are the conditions for a Deadlock to occur?", "short", "remember", "medium", 3, None, "Mutual exclusion, Hold and Wait, No Preemption, Circular Wait."),
            ("Explain the difference between Paging and Segmentation.", "short", "analyze", "medium", 3, None, "Paging: fixed blocks; Segmentation: logical variable segments."),
            ("Describe the concept of 'Belady's Anomaly' in Page Replacement.", "short", "understand", "medium", 3, None, "Faults increase when page frames increase (occurs in FIFO)."),
            ("What is a System Call? Name three categories.", "short", "remember", "medium", 3, None, "Interface between program and OS; Process, File, Device management."),
            ("Explain the concept of 'Thrashing'.", "short", "understand", "medium", 3, None, "High paging activity causes low CPU utilization."),
            ("Compare FCFS, SJF, and Round Robin scheduling algorithms.", "long", "analyze", "medium", 5, None, "Efficiency vs Fairness vs Waiting time trade-offs."),
            ("Explain the Producer-Consumer problem and its solution using Semaphores.", "long", "apply", "hard", 5, None, "Synchronization of buffer access."),
            ("Design a process scheduling simulator using Priority Preemptive algorithm logic.", "long", "create", "hard", 10, None, "Gantt chart and Average Waiting Time calculation logic."),
            ("Critically evaluate the design of Modern Microkernels versus Monolithic Kernels.", "long", "evaluate", "hard", 10, None, "Performance, security, and stability implications.")
        ],
        "Cyber Security": [
            ("Which 'A' in CIA ensures data is only accessed by authorized people?", "mcq", "remember", "easy", 1, ("Availability", "Accountability", "Authenticity", "Confidentiality"), "Confidentiality"),
            ("HTTPS uses which port for communication?", "mcq", "remember", "easy", 1, ("80", "110", "443", "53"), "443"),
            ("A 'Phishing' attack primarily targets:", "mcq", "understand", "easy", 1, ("Hardware", "OS vulnerability", "Human psychology", "Network bandwidth"), "Human psychology"),
            ("Which encryption uses two different keys (Public and Private)?", "mcq", "remember", "easy", 1, ("Symmetric", "Asymmetric", "Hashing", "Encoding"), "Asymmetric"),
            ("What does a Firewall do?", "mcq", "understand", "easy", 1, ("Scans for viruses", "Filters network traffic", "Encrypts files", "Boosts internet speed"), "Filters network traffic"),
            ("Define 'Ransomware' and how it impacts organizations.", "short", "understand", "medium", 3, None, "Malware that encrypts data and demands payment for release."),
            ("What is the difference between a Vulnerability, a Threat, and a Risk?", "short", "analyze", "medium", 3, None, "Vulnerability: weakness; Threat: potential exploit; Risk: probability of impact."),
            ("Explain the concept of 'Zero Day' vulnerability.", "short", "understand", "medium", 3, None, "A security flaw discovered by attackers before the developer is aware."),
            ("What is 'Two-Factor Authentication' (2FA)?", "short", "remember", "medium", 3, None, "Security layer requiring two forms of ID (e.g., password + OTP)."),
            ("Explain the 'Cross-Site Scripting' (XSS) attack vector.", "short", "understand", "medium", 3, None, "Injecting malicious scripts into trusted websites accessed by users."),
            ("Describe the phases of an Ethical Hacking engagement (VAPT).", "long", "remember", "medium", 5, None, "Recon, Scanning, Gaining Access, Maintaining, Clearing tracks."),
            ("Explain how Digital Signatures provide non-repudiation.", "long", "analyze", "hard", 5, None, "Linking user identity to a message via private key encryption."),
            ("Design a security policy for a remote-working software firm to guard against insider threats.", "long", "create", "hard", 10, None, "DLP, VPN, IAM, and audit logging strategies."),
            ("Evaluate the impact of Quantum Computing on current RSA and ECC encryption standards.", "long", "evaluate", "hard", 10, None, "Shor's algorithm and the need for Post-Quantum Cryptography.")
        ],
        "COA": [
            ("Which component performs mathematical operations?", "mcq", "remember", "easy", 1, ("CU", "Registers", "ALU", "Cache"), "ALU"),
            ("Which memory is fastest?", "mcq", "remember", "easy", 1, ("RAM", "Cache", "HDD", "Registers"), "Registers"),
            ("The 'Bottleneck' in computer architecture refers to:", "mcq", "understand", "medium", 1, ("Memory mismatch", "CPU overheating", "Slow bus", "Von Neumann Bottleneck"), "Von Neumann Bottleneck"),
            ("Increasing word size primarily improves:", "mcq", "understand", "medium", 1, ("Screen resolution", "Precision and Speed", "Color depth", "Storage space"), "Precision and Speed"),
            ("What is 'Pipelining' primarily used for?", "mcq", "understand", "medium", 1, ("Large RAM", "Parallelism in instruction execution", "Backup", "Graphics"), "Parallelism in instruction execution"),
            ("Explain the Von Neumann Architecture.", "short", "understand", "medium", 3, None, "Stored-program concept where instructions and data share same memory."),
            ("What is the difference between RISC and CISC?", "short", "analyze", "medium", 3, None, "RISC: simple instructions, single cycle; CISC: complex, multi-cycle."),
            ("Describe the function of 'Buses' in a computer system.", "short", "remember", "medium", 3, None, "Pathways for data, address, and control signals exchange."),
            ("Explain the concept of 'Instruction Pipelining' and its Hazards.", "short", "understand", "medium", 3, None, "Executing multiple instructions simultaneously; Structural, Data, Control hazards."),
            ("What is DMA (Direct Memory Access)?", "short", "remember", "medium", 3, None, "Bypassing CPU for high-speed I/O-to-memory data transfer."),
            ("Elaborate on the Memory Hierarchy and the principle of Locality.", "long", "understand", "medium", 5, None, "Speed vs Cost vs Size trade-off; Temporal and Spatial locality."),
            ("Describe the Cache Mapping techniques: Direct, Associative, and Set-Associative.", "long", "analyze", "hard", 5, None, "Placement and retrieval logic for cache data."),
            ("Calculate the effective memory access time for a system with 90% cache hit ratio.", "long", "apply", "medium", 10, None, "Formula: h*Tc + (1-h)*Tm with step-by-step calculation."),
            ("Evaluate the benefits of Multicore architectures compared to Single-core overclocking.", "long", "evaluate", "hard", 10, None, "Power dissipation, parallel throughput, and software scaling challenges.")
        ],
        "OOPs": [
            ("Wrapping data and functions into a single unit is called:", "mcq", "remember", "easy", 1, ("Inheritance", "Polymorphism", "Encapsulation", "Abstraction"), "Encapsulation"),
            ("Which member of a class is accessible only inside the class?", "mcq", "remember", "easy", 1, ("Public", "Private", "Protected", "Internal"), "Private"),
            ("A class serves as a _________ for objects.", "mcq", "understand", "easy", 1, ("Instance", "Blueprint", "Collection", "Binary file"), "Blueprint"),
            ("Function overloading is an example of:", "mcq", "understand", "medium", 1, ("Static polymorphism", "Dynamic polymorphism", "Inheritance", "Binding"), "Static polymorphism"),
            ("Which keyword is used to refer to the current object?", "mcq", "remember", "easy", 1, ("self", "this", "me", "parent"), "this"),
            ("Explain the concept of 'Inheritance' and its types.", "short", "understand", "medium", 3, None, "Mechanism to derive classes; Single, Multiple, Hierarchical, Multilevel, Hybrid."),
            ("What is an 'Abstract Class' and why is it used?", "short", "understand", "medium", 3, None, "Incomplete class that cannot be instantiated; used as a template for children."),
            ("Describe the difference between Method Overloading and Method Overriding.", "short", "analyze", "medium", 3, None, "Overloading: same class, diff params; Overriding: child redefines parent method."),
            ("What is the purpose of a 'Constructor'?", "short", "remember", "medium", 3, None, "Special method called automatically when an object is created to initialize it."),
            ("Explain 'Polymorphism' with a real-world example.", "short", "understand", "medium", 3, None, "One interface, multiple forms (e.g., a 'Shape' draw() method)."),
            ("Explain the four pillars of OOP with brief examples.", "long", "understand", "medium", 5, None, "Encapsulation, Abstraction, Inheritance, Polymorphism."),
            ("Describe 'Interface' vs 'Abstract Class' in context of Java or C#.", "long", "analyze", "medium", 5, None, "Contract vs Template with partial implementation."),
            ("Design a Class Hierarchy for an Electronic Commerce System (Users, Products, Orders).", "long", "create", "hard", 10, None, "Inheritance patterns and member identification."),
            ("Evaluate the pros and cons of using Multiple Inheritance in programming design.", "long", "evaluate", "hard", 10, None, "Power vs Collision (Diamond Problem) and complexity.")
        ]
    }

    try:
        inserted = 0
        for subj_name, questions in all_data.items():
            s_id = subjects.get(subj_name)
            if not s_id:
                print(f"Warning: Subject {subj_name} not found, skipping...")
                continue
            
            for q in questions:
                # Unpack and fix options format if necessary
                text, q_type, blooms, diff, marks, opts, ans = q
                insert_question(cur, s_id, text, q_type, blooms, diff, marks, opts, ans)
                inserted += 1
        
        con.commit()
        print(f"Successfully seeded {inserted} questions (14 per subject).")
    except Exception as e:
        con.rollback()
        print(f"Error: {e}")
    finally:
        con.close()

if __name__ == "__main__":
    seed()
