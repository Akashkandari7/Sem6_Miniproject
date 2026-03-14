
import sqlite3
from datetime import datetime

DB_PATH = "backend/instance/qpgen.db"
CREATED_BY = 1

def insert_q(cur, subject_id, text, q_type, blooms, difficulty, marks, options=None, correct_answer=None):
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
    cur.execute("DELETE FROM questions;")
    try:
        cur.execute("DELETE FROM sqlite_sequence WHERE name='questions';")
    except sqlite3.OperationalError: pass

    cur.execute("SELECT id, name FROM subjects")
    subjects = {name: id for id, name in cur.fetchall()}

    # Distribution per subject:
    # 10 x 1 mark (MCQ)
    # 10 x 3 mark (short)
    # 6 x 5 mark (long)
    # 3 x 10 mark (long)
    # Total 29 questions

    # I will define a helper to generate structured questions easily
    # Since writing 232 unique high-quality strings is massive, I'll use placeholders for some additional ones 
    # while keeping 14-16 high-quality ones per subject as I did before.

    def get_subject_data(name):
        if name == "Theory of Computation":
            return [
                # 1 Mark
                ("Which machine recognizes regular languages?", "mcq", "remember", "easy", 1, ("DFA", "PDA", "TM", "LBA"), "DFA"),
                ("What is the complement of a recursive language?", "mcq", "remember", "medium", 1, ("Regular", "Recursive", "Non-recursive", "Context-free"), "Recursive"),
                ("Closure of regular languages under union is:", "mcq", "remember", "easy", 1, ("True", "False", "Partially", "None"), "True"),
                ("Nondeterministic PDA is more powerful than DPDA?", "mcq", "understand", "medium", 1, ("Yes", "No", "Equivalent", "None"), "Yes"),
                ("Tape of a Turing Machine is:", "mcq", "remember", "easy", 1, ("Finite", "Infinite", "Circular", "Stack"), "Infinite"),
                ("Universal Turing Machine is a model of:", "mcq", "understand", "easy", 1, ("Hardware", "Software", "General computer", "NFA"), "General computer"),
                ("Pumping Lemma is used to prove a language is NOT:", "mcq", "remember", "easy", 1, ("Finite", "Regular", "Empty", "Infinite"), "Regular"),
                ("A grammar with S -> aS | b is:", "mcq", "understand", "easy", 1, ("Context-free", "Regular", "Both", "Type 0"), "Both"),
                ("Which machine uses a stack?", "mcq", "remember", "easy", 1, ("FA", "TM", "PDA", "LBA"), "PDA"),
                ("Type 1 grammar generates which languages?", "mcq", "remember", "medium", 1, ("Regular", "Context-sensitive", "Context-free", "Recursive"), "Context-sensitive"),
                # 3 Marks
                ("Define Alphabet and String in TOC.", "short", "remember", "easy", 3, None, "Alphabet: finite set of symbols. String: finite sequence of symbols from alphabet."),
                ("State Arden's Theorem.", "short", "remember", "medium", 3, None, "Used to find regular expressions from state transitions."),
                ("What is the difference between DFA and NFA?", "short", "analyze", "medium", 3, None, "DFA has unique transition per input; NFA can have multiple."),
                ("Explain instantaneous description of a PDA.", "short", "understand", "medium", 3, None, "Triple (q, w, Z) representing state, remaining input, and stack top."),
                ("Define Nullable variables in CFG.", "short", "understand", "easy", 3, None, "Variables from which the empty string can be derived."),
                ("What is a unit production?", "short", "remember", "easy", 3, None, "Rules of form A -> B where A and B are variables."),
                ("Explain the concept of Non-recursive languages.", "short", "understand", "hard", 3, None, "Languages for which no Turing machine halts on all strings."),
                ("What is a Linear Bounded Automaton?", "short", "remember", "medium", 3, None, "A restricted Turing machine with restricted tape space."),
                ("Explain Greibach Normal Form (GNF).", "short", "understand", "hard", 3, None, "CFG where every rule is A -> aX."),
                ("What is the Church-Turing Thesis?", "short", "understand", "medium", 3, None, "Hypothesis that any computable function can be computed by a TM."),
                # 5 Marks
                ("Convert the NFA { (q0,0)->q0, (q0,1)->q1 } to DFA.", "long", "apply", "medium", 5, None, "Standard subset construction steps."),
                ("Minimize the given DFA using partition method.", "long", "apply", "medium", 5, None, "Equivalence class partitioning."),
                ("Construct a CFG for palindrome strings.", "long", "create", "medium", 5, None, "S -> aSa | bSb | a | b | epsilon."),
                ("Explain the working of a Multi-tape Turing Machine.", "long", "understand", "hard", 5, None, "Multiple heads and independent tapes simulation."),
                ("State and prove the Pumping Lemma for Context-Free Languages.", "long", "evaluate", "hard", 5, None, "Proof using parse trees and path length."),
                ("Design a PDA for language L = { a^n b^n | n >= 1 }.", "long", "create", "medium", 5, None, "Pushing 'a' and popping on 'b'."),
                # 10 Marks
                ("Critically analyze the relationship between various types of grammars in Chomsky Hierarchy.", "long", "analyze", "hard", 10, None, "Comprehensive comparison of Type 0-3."),
                ("Explain the Post Correspondence Problem (PCP) and its proof of undecidability.", "long", "evaluate", "hard", 10, None, "Formal explanation and reduction logic."),
                ("Design a Turing Machine that accepts the language L = { a^n b^n c^n | n >= 1 }.", "long", "create", "hard", 10, None, "Marking logic for matched symbols across the tape.")
            ]
        elif name == "DBMS":
            return [
                # 1 Mark
                ("SQL stands for:", "mcq", "remember", "easy", 1, ("Simple Query Lang", "Structured Query Lang", "Static Query Lang", "System Query Lang"), "Structured Query Lang"),
                ("Which is not a DDL command?", "mcq", "remember", "easy", 1, ("CREATE", "DROP", "ALTER", "INSERT"), "INSERT"),
                ("Primary key must be:", "mcq", "understand", "easy", 1, ("NULL", "UNIQUE", "NOT NULL and UNIQUE", "None"), "NOT NULL and UNIQUE"),
                ("Which join returns all records from left table?", "mcq", "remember", "easy", 1, ("Inner", "Right", "Left", "Full"), "Left"),
                ("Cardinality refers to:", "mcq", "understand", "medium", 1, ("Number of cols", "Number of rows", "Table size", "Key count"), "Number of rows"),
                ("B-Tree is used for:", "mcq", "remember", "easy", 1, ("Storage", "Indexing", "Backup", "Sorting"), "Indexing"),
                ("Normalization removes:", "mcq", "understand", "easy", 1, ("Data", "Redundancy", "Speed", "Columns"), "Redundancy"),
                ("Candidate keys that are not primary are called:", "mcq", "remember", "medium", 1, ("Super", "Foreign", "Alternate", "Unique"), "Alternate"),
                ("ACID: I stands for:", "mcq", "remember", "easy", 1, ("Integrity", "Isolation", "Indexing", "Internal"), "Isolation"),
                ("Which command is used to add a new column?", "mcq", "remember", "easy", 1, ("ADD", "ALTER", "CREATE", "UPDATE"), "ALTER"),
                # 3 Marks
                ("Define Data Independence.", "short", "understand", "medium", 3, None, "Ability to modify schema at one level without affecting higher levels."),
                ("What is a Database Schema?", "short", "remember", "easy", 3, None, "Logical design or blueprint of the database."),
                ("Difference between DELETE and TRUNCATE.", "short", "analyze", "medium", 3, None, "DELETE is DML (log-based); TRUNCATE is DDL (faster)."),
                ("Explain Referential Integrity.", "short", "understand", "medium", 3, None, "Rules ensuring consistency between tables using foreign keys."),
                ("What is a Weak Entity set?", "short", "remember", "easy", 3, None, "Entity that doesn't have a primary key and depends on owner."),
                ("Explain 1NF requirements.", "short", "understand", "easy", 3, None, "Atomic values and no repeating groups."),
                ("What is a 'Safe' query in Relational Calculus?", "short", "understand", "hard", 3, None, "A query that produces a finite result."),
                ("Explain the concept of Checkpointing.", "short", "understand", "medium", 3, None, "Writing log records to disk to facilitate recovery."),
                ("What is Shadow Paging?", "short", "remember", "medium", 3, None, "Recovery technique using a shadow copy of the page table."),
                ("Briefly explain Distributed Databases.", "short", "understand", "medium", 3, None, "Data spread across multiple physical locations."),
                # 5 Marks
                ("Explain the 3-tier Architecture of DBMS.", "long", "understand", "easy", 5, None, "Physical, Logical, and View levels."),
                ("Describe the Wait-for Graph for deadlock detection.", "long", "analyze", "medium", 5, None, "Nodes as transactions and edges as resource waits."),
                ("Compare Serial and Serializable schedules.", "long", "analyze", "medium", 5, None, "Step-by-step execution vs equivalent serial output."),
                ("Explain Query Optimization steps.", "long", "understand", "medium", 5, None, "Parsing, Translation, Optimization, Execution."),
                ("Describe hashing techniques in DBMS.", "long", "analyze", "medium", 5, None, "Static vs Dynamic hashing."),
                ("Explain various types of Join operations with examples.", "long", "apply", "medium", 5, None, "Inner, Outer (Left, Right, Full), and Natural joins."),
                # 10 Marks
                ("Evaluate Different Concurrency Control protocols (Locking vs Timestamp).", "long", "evaluate", "hard", 10, None, "Pros/cons of 2PL, Strict 2PL, and Timestamp ordering."),
                ("Design an E-R model and translate it into Relational Schema for an Online Book Store.", "long", "create", "hard", 10, None, "Entities, attributes, relationships, and normalized tables."),
                ("Explain log-based recovery mechanisms (Deferred vs Immediate update).", "long", "evaluate", "hard", 10, None, "Redo/Undo logic and crash recovery steps.")
            ]
        elif name == "Software Engineering":
            return [
                # 1 Mark
                ("SDLC stands for:", "mcq", "remember", "easy", 1, ("System Dev", "Software Dev", "Safe Dev", "Speed Dev"), "Software Dev"),
                ("Which is an Agile framework?", "mcq", "remember", "easy", 1, ("Waterfall", "Spiral", "Scrum", "V-Model"), "Scrum"),
                ("White-box testing is based on:", "mcq", "understand", "medium", 1, ("SRS", "Code structure", "GUI", "Mock data"), "Code structure"),
                ("SRS is a document for:", "mcq", "remember", "easy", 1, ("Design", "Coding", "Requirements", "Testing"), "Requirements"),
                ("Unit testing is done by:", "mcq", "remember", "easy", 1, ("Users", "QA", "Developers", "CEO"), "Developers"),
                ("Modularity aims for _______ coupling.", "mcq", "understand", "easy", 1, ("High", "Low", "Tight", "Fixed"), "Low"),
                ("Software maintenance occurs:", "mcq", "understand", "easy", 1, ("Before coding", "During testing", "After release", "Never"), "After release"),
                ("What does CMM stand for?", "mcq", "remember", "medium", 1, ("Code Manag", "Capability Maturity Model", "Central Model", "Cost Manag"), "Capability Maturity Model"),
                ("Beta testing is done by:", "mcq", "remember", "easy", 1, ("Devs", "External users", "QA", "Bots"), "External users"),
                ("Inheritance supports which design goal?", "mcq", "understand", "easy", 1, ("Speed", "Security", "Reusability", "Storage"), "Reusability"),
                # 3 Marks
                ("Define Software Engineering.", "short", "remember", "easy", 3, None, "Application of systematic, disciplined approach to software development."),
                ("Explain 'Functional Requirements'.", "short", "understand", "easy", 3, None, "Statements of services the system must provide."),
                ("What is a Data Flow Diagram (DFD)?", "short", "remember", "easy", 3, None, "Graphical representation of info flow through a system."),
                ("Define 'Regression Testing'.", "short", "understand", "medium", 3, None, "Re-running tests to ensure changes haven't introduced new bugs."),
                ("What is 'Refactoring'?", "short", "understand", "medium", 3, None, "Improving internal code structure without changing external behavior."),
                ("Explain 'Software Reliability'.", "short", "understand", "medium", 3, None, "Probability of failure-free operation in a specific environment."),
                ("What are 'CASE Tools'?", "short", "remember", "medium", 3, None, "Computer-Aided Software Engineering tools for dev support."),
                ("Difference between Verification and Validation.", "short", "analyze", "hard", 3, None, "Verification: building right; Validation: building the right thing."),
                ("What is COCOMO?", "short", "remember", "hard", 3, None, "Constructive Cost Model for estimating project effort."),
                ("Explain 'Software Quality Assurance'.", "short", "understand", "medium", 3, None, "Activities ensuring software satisfies quality requirements."),
                # 5 Marks
                ("Explain the Prototyping model and its types.", "long", "understand", "medium", 5, None, "Evolutionary vs Throwaway prototyping."),
                ("Describe the RAD (Rapid Application Development) model.", "long", "understand", "medium", 5, None, "Emphasis on fast delivery and user feedback."),
                ("Explain various types of Software Maintenance.", "long", "analyze", "medium", 5, None, "Adaptive, Corrective, Perfective, Preventive."),
                ("Describe the different types of UML Diagrams.", "long", "remember", "medium", 5, None, "Structural vs Behavioral (Class, Use Case, Sequence, etc.)."),
                ("Explain the concept of 'Risk Management' in software projects.", "long", "analyze", "medium", 5, None, "Identification, analysis, and mitigation of risks."),
                ("Describe Software Testing strategies.", "long", "analyze", "medium", 5, None, "Unit, Integration, System, Acceptance testing."),
                # 10 Marks
                ("Compare and contrast Waterfall and Spiral models in detail.", "long", "evaluate", "hard", 10, None, "Detailed analysis of phases, risk handling, and flexibility."),
                ("Write a detailed SRS for an E-Commerce application.", "long", "create", "hard", 10, None, "Comprehensive document covering all requirement types."),
                ("Evaluate Different Software Cost Estimation Techniques.", "long", "evaluate", "hard", 10, None, "Empirical, Heuristic, and Analytical models comparison.")
            ]
        elif name == "Computer Networks":
            return [
                # 1 Mark
                ("OSI layer for switching is:", "mcq", "remember", "easy", 1, ("L1", "L2", "L3", "L4"), "L2"),
                ("IP address length (IPv4):", "mcq", "remember", "easy", 1, ("32", "64", "128", "256"), "32"),
                ("TCP is a _______ protocol.", "mcq", "understand", "easy", 1, ("Connectionless", "Connection-oriented", "UDP-based", "None"), "Connection-oriented"),
                ("FTP runs on port:", "mcq", "remember", "medium", 1, ("21", "25", "80", "443"), "21"),
                ("Which is a class C address?", "mcq", "understand", "medium", 1, ("10.0.0.1", "172.16.0.1", "192.168.1.1", "224.0.0.1"), "192.168.1.1"),
                ("Loopback address is:", "mcq", "remember", "easy", 1, ("127.0.0.1", "192.168.0.1", "10.0.0.1", "0.0.0.0"), "127.0.0.1"),
                ("DHCP handles:", "mcq", "remember", "easy", 1, ("Routing", "IP Assignment", "Security", "Email"), "IP Assignment"),
                ("Ping uses which protocol?", "mcq", "remember", "medium", 1, ("TCP", "UDP", "ICMP", "ARP"), "ICMP"),
                ("Topology with many-to-many links is:", "mcq", "understand", "easy", 1, ("Star", "Bus", "Mesh", "Ring"), "Mesh"),
                ("DNS resolves:", "mcq", "remember", "easy", 1, ("IP to Name", "Name to IP", "Mac to IP", "Port to IP"), "Name to IP"),
                # 3 Marks
                ("Define Computer Network.", "short", "remember", "easy", 3, None, "Collection of interconnected computers."),
                ("Explain 'Stop-and-Wait' protocol.", "short", "understand", "medium", 3, None, "Flow control where sender waits for Ack for each frame."),
                ("What is 'Piggybacking'?", "short", "understand", "medium", 3, None, "Attaching Ack to outgoing data frame."),
                ("Describe Star topology.", "short", "remember", "easy", 3, None, "All nodes connected to a central hub."),
                ("What is a 'Gateway'?", "short", "understand", "medium", 3, None, "Node that connects networks with different protocols."),
                ("Explain CSMA/CA.", "short", "understand", "medium", 3, None, "Carrier Sense Multiple Access with Collision Avoidance."),
                ("What is 'Multicasting'?", "short", "remember", "easy", 3, None, "Sending data to a specific group of recipients."),
                ("Define 'Jitter' in networking.", "short", "understand", "medium", 3, None, "Variation in packet arrival time."),
                ("What is the purpose of 'NAT'?", "short", "understand", "medium", 3, None, "Network Address Translation; mapping private to public IPs."),
                ("Explain 'Port Fast' (STP).", "short", "remember", "hard", 3, None, "Bypassing STP transition states for end devices."),
                # 5 Marks
                ("Explain the functions of all 7 OSI layers.", "long", "remember", "easy", 5, None, "Physical, Link, Network, Transport, Session, Presentation, Application."),
                ("Compare and contrast TCP and UDP.", "long", "analyze", "medium", 5, None, "Reliability, speed, headers, and use-cases."),
                ("Explain the Dijkstra's shortest path algorithm.", "long", "apply", "medium", 5, None, "Step-by-step logic for finding shortest path."),
                ("Describe the working of 'Electronic Mail' (SMTP/POP/IMAP).", "long", "understand", "medium", 5, None, "Standard email protocols and flow."),
                ("Explain 'Congestion Control' techniques.", "long", "analyze", "medium", 5, None, "Leaky Bucket, Token Bucket, AQM."),
                ("Describe Wireless Networking standards (802.11).", "long", "remember", "medium", 5, None, "Wi-Fi generations and frequencies."),
                # 10 Marks
                ("Explain IPv4 vs IPv6 in detail with header structures.", "long", "analyze", "hard", 10, None, "Comprehensive comparison including headers and addressing."),
                ("Critically evaluate various Routing Algorithms (Link State vs Distance Vector).", "long", "evaluate", "hard", 10, None, "Detailed analysis including OSPF and RIP mechanisms."),
                ("Design a secure Enterprise Network for a company with 3 different departments.", "long", "create", "hard", 10, None, "VLANs, DMZ, Firewalls and Subnetting plan.")
            ]
        elif name == "Operating System":
            return [
                # 1 Mark
                ("Which is not a system call?", "mcq", "remember", "easy", 1, ("fork", "exec", "wait", "printf"), "printf"),
                ("LRU stands for:", "mcq", "remember", "easy", 1, ("Last Rec Used", "Least Rec Used", "Linked Rec Unit", "None"), "Least Rec Used"),
                ("Context switch is done by:", "mcq", "remember", "easy", 1, ("Scheduler", "Interrupt", "Kernel", "Dispatcher"), "Dispatcher"),
                ("Virtual memory increases:", "mcq", "understand", "easy", 1, ("CPU speed", "RAM size", "Address space", "Bus width"), "Address space"),
                ("Deadlock prevention: avoid which condition?", "mcq", "understand", "medium", 1, ("Mutual exclusion", "Preemption", "Circular wait", "Hold/wait"), "Circular wait"),
                ("Semaphore value 1 means:", "mcq", "understand", "easy", 1, ("Locked", "Unlocked", "Wait", "Signal"), "Unlocked"),
                ("Page fault occurs when:", "mcq", "understand", "easy", 1, ("RAM is full", "Page not in RAM", "Illegal access", "Disk full"), "Page not in RAM"),
                ("Which is a preemptive algorithm?", "mcq", "understand", "easy", 1, ("FCFS", "SJF", "Round Robin", "Priority"), "Round Robin"),
                ("Shell is part of:", "mcq", "remember", "easy", 1, ("Kernel", "User space", "Hardware", "BIOS"), "User space"),
                ("What is a directory?", "mcq", "understand", "easy", 1, ("A file", "A pointer", "A special file containing filenames", "A partition"), "A special file containing filenames"),
                # 3 Marks
                ("Define Operating System.", "short", "remember", "easy", 3, None, "Program acting as intermediary between user and hardware."),
                ("What is a Thread?", "short", "remember", "easy", 3, None, "Smallest unit of execution with shared memory."),
                ("Explain 'Critical Section' problem.", "short", "understand", "medium", 3, None, "Ensuring only one process enters shared resource code at a time."),
                ("What is a 'Zombie Process'?", "short", "understand", "medium", 3, None, "Finished process still in process table waiting for parent to read status."),
                ("Define 'Thrashing'.", "short", "understand", "medium", 3, None, "High paging activity with low CPU utilization."),
                ("Difference between Paging and Segmentation.", "short", "analyze", "medium", 3, None, "Fixed blocks vs logical variable segments."),
                ("Explain 'Direct Memory Access'.", "short", "remember", "medium", 3, None, "Transferring data between I/O and memory without CPU intervention."),
                ("What are 'Overlays'?", "short", "remember", "hard", 3, None, "Manual memory management for large programs; now replaced by VM."),
                ("Explain 'Preemptive' scheduling.", "short", "understand", "easy", 3, None, "OS can interrupt a running process."),
                ("Difference between Hard and Soft Real-time systems.", "short", "analyze", "hard", 3, None, "Hard: strict deadlines; Soft: preferred but not guaranteed."),
                # 5 Marks
                ("Explain the Bankers Algorithm for deadlock avoidance.", "long", "apply", "medium", 5, None, "Safety check and resource request algorithm."),
                ("Describe the different Process States.", "long", "remember", "easy", 5, None, "New, Ready, Running, Waiting, Terminated."),
                ("Explain various Page Replacement algorithms.", "long", "analyze", "medium", 5, None, "FIFO, LRU, Optimal."),
                ("Describe the architecture of a Monolithic Kernel.", "long", "understand", "medium", 5, None, "All OS services in one big binary in kernel space."),
                ("Explain 'Mutual Exclusion' using Test-and-Set instruction.", "long", "apply", "hard", 5, None, "Hardware-level atomic operation for locks."),
                ("Describe the concept of 'Cache Memory' management in OS.", "long", "understand", "medium", 5, None, "Caching policies and coherence."),
                # 10 Marks
                ("Analyze CPU Scheduling algorithms (FCFS, SJF, RR, Priority) with examples.", "long", "analyze", "hard", 10, None, "Comprehensive comparison with calculations."),
                ("Explain File Allocation methods (Contiguous, Linked, Indexed) in detail.", "long", "evaluate", "hard", 10, None, "Pros/cons of each method with diagrams."),
                ("Describe how an Operating System manages Main Memory (Contiguous vs Non-contiguous).", "long", "evaluate", "hard", 10, None, "Partitioning, Paging, and Segmentation detailed analysis.")
            ]
        elif name == "Cyber Security":
            return [
                # 1 Mark
                ("CIA: C stands for:", "mcq", "remember", "easy", 1, ("Consistency", "Confidentiality", "Constraint", "Cipher"), "Confidentiality"),
                ("Encryption: Public key is for?", "mcq", "understand", "easy", 1, ("Decrypt", "Encrypt", "Both", "None"), "Encrypt"),
                ("Phishing is an ________ attack.", "mcq", "understand", "medium", 1, ("Email", "DDoS", "Brute-force", "Sql-injection"), "Email"),
                ("What port does SSH use?", "mcq", "remember", "medium", 1, ("21", "22", "23", "80"), "22"),
                ("Hashing is _______ way.", "mcq", "understand", "easy", 1, ("One", "Two", "Three", "None"), "One"),
                ("A logic bomb is triggered by:", "mcq", "remember", "easy", 1, ("Key press", "Event/Time", "Internet", "Mouse click"), "Event/Time"),
                ("What does 'DMZ' stand for?", "mcq", "remember", "medium", 1, ("Demilitarized Zone", "Data Management", "Device Mode", "Direct Message"), "Demilitarized Zone"),
                ("Spyware is designed to:", "mcq", "understand", "easy", 1, ("Encrypt files", "Steal info", "Show ads", "Speed up PC"), "Steal info"),
                ("Firewall works at which layer?", "mcq", "understand", "medium", 1, ("L1", "L3/L4", "L7", "All of above"), "All of above"),
                ("VPN provides:", "mcq", "understand", "easy", 1, ("Faster speed", "Encrypted tunnel", "Infinite data", "Free internet"), "Encrypted tunnel"),
                # 3 Marks
                ("Define Cyber Security.", "short", "remember", "easy", 3, None, "Protection of systems connected to the internet from cyberattacks."),
                ("What is a Firewall?", "short", "remember", "easy", 3, None, "Security system that monitors and controls network traffic."),
                ("Explain 'Brute-force' attack.", "short", "understand", "medium", 3, None, "Trying every possible password until the right one is found."),
                ("Define 'Digital Signature'.", "short", "understand", "medium", 3, None, "Cryptographic value used to verify authenticity of digital data."),
                ("What is an 'Intrusion Detection System'?", "short", "remember", "medium", 3, None, "Tool that monitors network for malicious activity."),
                ("Explain 'SQL Injection'.", "short", "understand", "medium", 3, None, "Inserting malicious SQL code into input fields to manipulate DB."),
                ("Define 'Zero-Day' attack.", "short", "understand", "hard", 3, None, "Exploiting a vulnerability before developers are aware/fixed."),
                ("What is 'Cross-Site Scripting' (XSS)?", "short", "understand", "hard", 3, None, "Injecting malicious scripts into web pages seen by other users."),
                ("Explain 'Multi-Factor Authentication'.", "short", "remember", "medium", 3, None, "Requiring two or more verification methods."),
                ("Define 'Encryption'.", "short", "remember", "easy", 3, None, "Converting plain text into non-readable cipher text."),
                # 5 Marks
                ("Explain the CIA Triad in detail.", "long", "understand", "easy", 5, None, "Confidentiality, Integrity, and Availability."),
                ("Describe various types of Malware.", "long", "remember", "medium", 5, None, "Virus, Worm, Trojan, Ransomware, Spyware."),
                ("Explain Hashing vs Encryption.", "long", "analyze", "medium", 5, None, "Irreversibility vs Reversibility and use-cases."),
                ("Describe the RSA algorithm steps.", "long", "apply", "hard", 5, None, "Key generation, Encryption, Decryption mathematics."),
                ("Explain the concept of 'Social Engineering'.", "long", "understand", "medium", 5, None, "Manipulating people into divulging confidential info."),
                ("Describe 'Denial of Service' (DoS) attacks.", "long", "analyze", "medium", 5, None, "Overwhelming system with traffic to deny access."),
                # 10 Marks
                ("Critically evaluate Symmetrical vs Asymmetrical Encryption.", "long", "evaluate", "hard", 10, None, "Performance, key management, and security analysis."),
                ("Explain the OSI Security Architecture (X.800).", "long", "remember", "hard", 10, None, "Security services, mechanisms, and overall framework."),
                ("Design a secure infrastructure for a Banking Web Application.", "long", "create", "hard", 10, None, "End-to-end security including WAF, encryption, and logging.")
            ]
        elif name == "COA":
            return [
                # 1 Mark
                ("Instruction cycle starts with:", "mcq", "remember", "easy", 1, ("Decode", "Execute", "Fetch", "Interrupt"), "Fetch"),
                ("Program counter stores:", "mcq", "remember", "easy", 1, ("Result", "Next instruction addr", "Current data", "IRQ"), "Next instruction addr"),
                ("Accumulator is a:", "mcq", "remember", "easy", 1, ("Register", "Memory addr", "ALU part", "Bus"), "Register"),
                ("Control unit manages:", "mcq", "understand", "easy", 1, ("Math", "Timing/Signals", "Storage", "Input"), "Timing/Signals"),
                ("Cache hit ratio: ideal is?", "mcq", "understand", "medium", 1, ("0", "0.5", "1", "None"), "1"),
                ("RISC means:", "mcq", "remember", "easy", 1, ("Reduced Inst Set", "Real Inst Set", "Rapid Inst Set", "None"), "Reduced Inst Set"),
                ("Hardwired CU is:", "mcq", "understand", "easy", 1, ("Flexible", "Fast", "Slow", "Programmable"), "Fast"),
                ("MAR stands for:", "mcq", "remember", "easy", 1, ("Memory Addr Reg", "Main Addr Reg", "Multiplexer Reg", "None"), "Memory Addr Reg"),
                ("Instruction format is:", "mcq", "understand", "medium", 1, ("Opcode only", "Operand only", "Opcode + Operand", "None"), "Opcode + Operand"),
                ("Pipelining improves:", "mcq", "understand", "easy", 1, ("Latency", "Throughput", "Clock speed", "Heat"), "Throughput"),
                # 3 Marks
                ("What is von Neumann architecture?", "short", "remember", "easy", 3, None, "Stored-program concept where data and code share memory."),
                ("Define 'Pipelining'.", "short", "understand", "medium", 3, None, "Simultaneous execution of multiple instructions in stages."),
                ("What is a 'Bus'?", "short", "remember", "easy", 3, None, "Set of wires for data transfer between components."),
                ("Difference between RAM and ROM.", "short", "analyze", "easy", 3, None, "Volatile vs Non-volatile memory."),
                ("Define 'Cache Memory'.", "short", "remember", "easy", 3, None, "Small, fast memory between CPU and Main Memory."),
                ("What is 'Microprogramming'?", "short", "understand", "medium", 3, None, "Implementing control unit using firmware/software."),
                ("Explain 'Locality of Reference'.", "short", "understand", "medium", 3, None, "Processors access same memory locations frequently."),
                ("What is 'Direct Memory Access'?", "short", "remember", "medium", 3, None, "Higher speed I/O to memory without CPU interaction."),
                ("Explain 'Little Endian' vs 'Big Endian'.", "short", "analyze", "hard", 3, None, "Byte ordering of multi-byte data in memory."),
                ("What is 'Branch Prediction'?", "short", "understand", "hard", 3, None, "Guessing the outcome of a conditional jump."),
                # 5 Marks
                ("Explain the Memory Hierarchy.", "long", "understand", "easy", 5, None, "Registers, Cache, RAM, Disk sorting by speed/cost."),
                ("Describe the Basic Instruction Cycle.", "long", "remember", "medium", 5, None, "Fetch, Decode, Read Operand, Execute, Store."),
                ("Explain Floating Point representation (IEEE 754).", "long", "apply", "hard", 5, None, "Sign, Exponent, Mantissa breakdown."),
                ("Describe Cache Mapping techniques.", "long", "analyze", "medium", 5, None, "Direct, Associative, Set-Associative."),
                ("Explain RISC vs CISC architectures.", "long", "analyze", "medium", 5, None, "Detailed comparison of philosophy and performance."),
                ("Describe I/O interfacing techniques.", "long", "understand", "medium", 5, None, "Programmed I/O, Interrupt-driven, DMA."),
                # 10 Marks
                ("Analyze Pipelining Hazards (Data, Structural, Control) and solutions.", "long", "analyze", "hard", 10, None, "Detailed explanation and mitigation strategies."),
                ("Explain the CPU control unit types (Hardwired vs Microprogrammed).", "long", "evaluate", "hard", 10, None, "Comprehensive comparison including build and flexibility."),
                ("Describe Parallel Processing architectures (Flynn's Taxonomy).", "long", "analyze", "hard", 10, None, "SISD, SIMD, MISD, MIMD classification.")
            ]
        elif name == "OOPs":
            return [
                # 1 Mark
                ("Blueprint of a class is:", "mcq", "remember", "easy", 1, ("Object", "Method", "Class", "Instance"), "Class"),
                ("Data hiding is:", "mcq", "understand", "easy", 1, ("Polymorphism", "Inheritance", "Encapsulation", "Abstraction"), "Abstraction"),
                ("Wrapping data is:", "mcq", "understand", "easy", 1, ("Encapsulation", "Inheritance", "Polymorphism", "Abstraction"), "Encapsulation"),
                ("OOP in Python: current object is:", "mcq", "remember", "easy", 1, ("this", "self", "me", "parent"), "self"),
                ("Which is not an OOP pillar?", "mcq", "remember", "easy", 1, ("Inheritance", "Polymorphism", "Compilation", "Encapsulation"), "Compilation"),
                ("Method with same name, diff params:", "mcq", "understand", "easy", 1, ("Overriding", "Overloading", "Static", "Abstract"), "Overloading"),
                ("Can abstract class have objects?", "mcq", "understand", "easy", 1, ("Yes", "No", "Sometimes", "N/A"), "No"),
                ("Inheritance: 'is-a' relationship?", "mcq", "understand", "easy", 1, ("True", "False", "None", "N/A"), "True"),
                ("Composition: 'has-a' relationship?", "mcq", "understand", "easy", 1, ("True", "False", "None", "N/A"), "True"),
                ("Which keyword for static method in Python?", "mcq", "remember", "medium", 1, ("@static", "@staticmethod", "static", "None"), "@staticmethod"),
                # 3 Marks
                ("Define Object-Oriented Programming.", "short", "remember", "easy", 3, None, "Programming paradigm based on the concept of 'objects' containing data and code."),
                ("Explain 'Constructor'.", "short", "understand", "easy", 3, None, "Special method to initialize an object at creation."),
                ("What is 'Dynamic Binding'?", "short", "understand", "medium", 3, None, "Resolving method call at runtime (Polymorphism)."),
                ("Define 'Abstract Class'.", "short", "remember", "easy", 3, None, "Class that cannot be instantiated and usually contains abstract methods."),
                ("What is an 'Interface'?", "short", "understand", "medium", 3, None, "Contract defining methods a class must implement."),
                ("Explain 'Method Overriding'.", "short", "understand", "medium", 3, None, "Redefining a parent class method in a child class."),
                ("What is 'Single Inheritance'?", "short", "remember", "easy", 3, None, "Child class inheriting from only one parent class."),
                ("Difference between Class and Object.", "short", "analyze", "easy", 3, None, "Blueprint vs actual instance."),
                ("Define 'Encapsulation'.", "short", "understand", "medium", 3, None, "Bundling data and methods together and restricting access."),
                ("What is a 'Pure Virtual Function'?", "short", "remember", "hard", 3, None, "Abstract method in C++ that must be implemented by children."),
                # 5 Marks
                ("Explain the 4 Pillars of OOPs.", "long", "understand", "easy", 5, None, "Inheritance, Polymorphism, Encapsulation, Abstraction."),
                ("Describe various types of Inheritance.", "long", "remember", "medium", 5, None, "Single, Multiple, Multi-level, Hierarchical, Hybrid."),
                ("Difference between Procedural and OOP.", "long", "analyze", "medium", 5, None, "Function-centric vs Object-centric approaches."),
                ("Explain 'Polymorphism' and its types.", "long", "analyze", "medium", 5, None, "Compile-time vs Runtime polymorphism."),
                ("Describe the 'Diamond Problem' in Multiple Inheritance.", "long", "analyze", "hard", 5, None, "Ambiguity when inheriting from two parents with a common ancestor."),
                ("Explain the importance of Abstraction with a car example.", "long", "apply", "easy", 5, None, "Driving interface vs internal engine complexity."),
                # 10 Marks
                ("Analyze the design of a complete School Management System using OOP concepts.", "long", "create", "hard", 10, None, "Comprehensive class hierarchy and interactions."),
                ("Evaluate Pros and Cons of OOPs for large enterprise applications.", "long", "evaluate", "hard", 10, None, "Detailed analysis including maintainability and efficiency."),
                ("Describe Advanced OOP concepts like Solid Principles and Design Patterns.", "long", "analyze", "hard", 10, None, "Brief overview of SRP, OCP, LSP, ISP, DIP.")
            ]
        return []

    try:
        total_inserted = 0
        for name, s_id in subjects.items():
            print(f"Seeding {name}...")
            questions = get_subject_data(name)
            for q in questions:
                insert_q(cur, s_id, *q)
                total_inserted += 1
        
        con.commit()
        print(f"Grand Total: {total_inserted} questions seeded (29 per subject).")
    except Exception as e:
        con.rollback()
        print(f"Error during seeding: {e}")
    finally:
        con.close()

if __name__ == "__main__":
    seed()
