"""
Seed script: inserts 10 questions for each of the 6 Bloom's taxonomy levels
into the questions table for subject_id=1 (Computer Science), created_by=2.

Run from the backend/ directory:
    python seed_questions.py
"""

import sqlite3
from datetime import datetime

DB_PATH = "instance/qpgen.db"
SUBJECT_ID = 1
CREATED_BY = 2
NOW = datetime.utcnow().isoformat()


def ins(cur, text, q_type, blooms, difficulty, marks,
        oa=None, ob=None, oc=None, od=None, ca=None):
    cur.execute(
        """INSERT INTO questions
           (text, question_type, blooms_level, difficulty, marks,
            option_a, option_b, option_c, option_d, correct_answer,
            subject_id, created_by, times_used, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,0,?)""",
        (text, q_type, blooms, difficulty, marks,
         oa, ob, oc, od, ca, SUBJECT_ID, CREATED_BY, NOW)
    )


QUESTIONS = {
    # ── 1. REMEMBER ──────────────────────────────────────────────────────────
    "remember": [
        # MCQ × 4
        dict(text="What does CPU stand for?",
             q_type="mcq", difficulty="easy", marks=1,
             oa="Central Processing Unit", ob="Central Program Utility",
             oc="Computer Processing Unit", od="Control Processing Unit",
             ca="Central Processing Unit"),
        dict(text="Which data structure uses LIFO (Last In First Out) order?",
             q_type="mcq", difficulty="easy", marks=1,
             oa="Queue", ob="Stack", oc="Linked List", od="Tree",
             ca="Stack"),
        dict(text="What is the base of the binary number system?",
             q_type="mcq", difficulty="easy", marks=1,
             oa="8", ob="10", oc="16", od="2",
             ca="2"),
        dict(text="Which of the following is NOT a programming paradigm?",
             q_type="mcq", difficulty="easy", marks=1,
             oa="Object-Oriented", ob="Functional", oc="Procedural", od="Sequential",
             ca="Sequential"),
        # Short × 4
        dict(text="Define an operating system.",
             q_type="short", difficulty="easy", marks=2,
             ca="An operating system is system software that manages computer hardware and software resources and provides services for computer programs."),
        dict(text="What is RAM?",
             q_type="short", difficulty="easy", marks=2,
             ca="RAM (Random Access Memory) is volatile primary memory used by the CPU to store data that is actively being used or processed."),
        dict(text="List the four basic operations of a computer.",
             q_type="short", difficulty="easy", marks=2,
             ca="Input, Processing, Storage, and Output."),
        dict(text="What is an algorithm?",
             q_type="short", difficulty="easy", marks=2,
             ca="An algorithm is a finite, ordered set of well-defined instructions used to solve a problem or perform a computation."),
        # Long × 2
        dict(text="State five generations of computers and identify the key technology used in each generation.",
             q_type="long", difficulty="medium", marks=5,
             ca="1st: Vacuum tubes; 2nd: Transistors; 3rd: Integrated circuits; 4th: Microprocessors; 5th: AI / parallel processing."),
        dict(text="List and briefly describe five common data types found in most programming languages.",
             q_type="long", difficulty="easy", marks=5,
             ca="Integer, Float, Boolean, Character, String – with brief descriptions of each."),
    ],

    # ── 2. UNDERSTAND ─────────────────────────────────────────────────────────
    "understand": [
        dict(text="Which statement best describes the purpose of an index in a database?",
             q_type="mcq", difficulty="easy", marks=1,
             oa="To store backup copies of data",
             ob="To speed up data retrieval operations",
             oc="To enforce referential integrity",
             od="To compress table data",
             ca="To speed up data retrieval operations"),
        dict(text="What is the difference between a compiler and an interpreter?",
             q_type="mcq", difficulty="medium", marks=1,
             oa="A compiler runs code line-by-line; an interpreter translates the entire program first",
             ob="A compiler translates the entire program before execution; an interpreter translates line-by-line",
             oc="Both do the same thing",
             od="An interpreter produces machine code; a compiler does not",
             ca="A compiler translates the entire program before execution; an interpreter translates line-by-line"),
        dict(text="Which OSI layer is responsible for end-to-end communication and error recovery?",
             q_type="mcq", difficulty="medium", marks=1,
             oa="Network Layer", ob="Data Link Layer",
             oc="Transport Layer", od="Session Layer",
             ca="Transport Layer"),
        dict(text="In object-oriented programming, what does 'encapsulation' mean?",
             q_type="mcq", difficulty="easy", marks=1,
             oa="Inheriting properties from a parent class",
             ob="Bundling data and methods that operate on the data within a single unit",
             oc="Having multiple forms of a method",
             od="Hiding the implementation of inherited methods",
             ca="Bundling data and methods that operate on the data within a single unit"),
        dict(text="Explain the concept of polymorphism in OOP with a simple example.",
             q_type="short", difficulty="medium", marks=3,
             ca="Polymorphism allows objects of different classes to be treated as objects of a common base class. E.g., a draw() method behaves differently for Circle and Rectangle objects."),
        dict(text="Describe the difference between stack and heap memory.",
             q_type="short", difficulty="medium", marks=3,
             ca="Stack is used for static memory allocation (local variables, function calls) and is managed automatically. Heap is used for dynamic memory allocation and must be managed by the programmer."),
        dict(text="Explain what a foreign key is and why it is used in relational databases.",
             q_type="short", difficulty="easy", marks=2,
             ca="A foreign key is a field (or set of fields) in one table that uniquely identifies a row in another table, used to maintain referential integrity between the two tables."),
        dict(text="Summarise how TCP/IP's three-way handshake establishes a connection.",
             q_type="short", difficulty="medium", marks=3,
             ca="Client sends SYN → Server replies with SYN-ACK → Client sends ACK. Connection is now established."),
        dict(text="Explain the difference between process and thread, and describe how they interact within an operating system.",
             q_type="long", difficulty="medium", marks=5,
             ca="A process is an independent program in execution with its own memory space. A thread is the smallest unit of execution within a process, sharing the process's memory. Multiple threads within a process can run concurrently, improving efficiency."),
        dict(text="Describe how a hash table works, including how collisions are handled.",
             q_type="long", difficulty="medium", marks=5,
             ca="A hash table maps keys to array indices via a hash function. Collisions (two keys mapping to the same index) are handled by chaining (linked lists at each index) or open addressing (probing for the next empty slot)."),
    ],

    # ── 3. APPLY ──────────────────────────────────────────────────────────────
    "apply": [
        dict(text="Given the array [5, 3, 8, 1, 9, 2], what is the array after one pass of bubble sort?",
             q_type="mcq", difficulty="medium", marks=1,
             oa="[1, 2, 3, 5, 8, 9]",
             ob="[3, 5, 1, 8, 2, 9]",
             oc="[3, 5, 8, 1, 2, 9]",
             od="[5, 3, 1, 8, 9, 2]",
             ca="[3, 5, 1, 8, 2, 9]"),
        dict(text="Which SQL clause would you use to filter results after grouping?",
             q_type="mcq", difficulty="easy", marks=1,
             oa="WHERE", ob="HAVING", oc="ORDER BY", od="GROUP BY",
             ca="HAVING"),
        dict(text="What is the output of: print(2 ** 3 + 1) in Python?",
             q_type="mcq", difficulty="easy", marks=1,
             oa="7", ob="9", oc="8", od="6",
             ca="9"),
        dict(text="A linked list has nodes: 10 → 20 → 30 → NULL. After deleting node 20, what does the list look like?",
             q_type="mcq", difficulty="medium", marks=1,
             oa="10 → 30 → NULL",
             ob="10 → NULL",
             oc="20 → 30 → NULL",
             od="10 → 20 → NULL",
             ca="10 → 30 → NULL"),
        dict(text="Write a Python function to check whether a given string is a palindrome.",
             q_type="short", difficulty="medium", marks=3,
             ca="def is_palindrome(s): return s == s[::-1]"),
        dict(text="Write an SQL query to find the second highest salary from an 'employees' table.",
             q_type="short", difficulty="medium", marks=3,
             ca="SELECT MAX(salary) FROM employees WHERE salary < (SELECT MAX(salary) FROM employees);"),
        dict(text="Implement a stack using a Python list with push and pop operations.",
             q_type="short", difficulty="medium", marks=3,
             ca="stack = []; stack.append(x)  # push; stack.pop()  # pop"),
        dict(text="Apply the binary search algorithm to find the value 45 in the sorted list [10, 20, 30, 40, 45, 50, 60]. Show all steps.",
             q_type="short", difficulty="medium", marks=4,
             ca="mid=40 (idx 3)<45, search right half; mid=50(idx 5)>45, search left; mid=45(idx 4) found."),
        dict(text="Write a Python program that reads a list of integers and prints only the even numbers using list comprehension.",
             q_type="long", difficulty="easy", marks=5,
             ca="numbers = [1,2,3,4,5,6]; evens = [n for n in numbers if n % 2 == 0]; print(evens)"),
        dict(text="Design and implement a class 'BankAccount' in Python with attributes balance and methods deposit(), withdraw(), and get_balance(). Include error handling for insufficient funds.",
             q_type="long", difficulty="hard", marks=10,
             ca="class BankAccount: def __init__(self): self.balance=0; def deposit(self,a): self.balance+=a; def withdraw(self,a): if a>self.balance: raise ValueError('Insufficient funds'); self.balance-=a; def get_balance(self): return self.balance"),
    ],

    # ── 4. ANALYZE ────────────────────────────────────────────────────────────
    "analyze": [
        dict(text="Which sorting algorithm has the best worst-case time complexity?",
             q_type="mcq", difficulty="medium", marks=1,
             oa="Bubble Sort", ob="Quick Sort",
             oc="Merge Sort", od="Selection Sort",
             ca="Merge Sort"),
        dict(text="In a relational database, which normal form eliminates transitive dependencies?",
             q_type="mcq", difficulty="medium", marks=1,
             oa="1NF", ob="2NF", oc="3NF", od="BCNF",
             ca="3NF"),
        dict(text="Analyze the time complexity of binary search.",
             q_type="mcq", difficulty="medium", marks=1,
             oa="O(n)", ob="O(n²)", oc="O(log n)", od="O(1)",
             ca="O(log n)"),
        dict(text="Which design pattern ensures that only one instance of a class is created?",
             q_type="mcq", difficulty="medium", marks=1,
             oa="Factory", ob="Observer", oc="Singleton", od="Decorator",
             ca="Singleton"),
        dict(text="Analyze the difference between BFS and DFS graph traversal algorithms. When would you prefer one over the other?",
             q_type="short", difficulty="hard", marks=4,
             ca="BFS uses a queue and explores level-by-level; best for shortest path. DFS uses a stack/recursion and explores depth-first; best for topological sort and cycle detection."),
        dict(text="Compare and contrast SQL and NoSQL databases, giving one use-case for each.",
             q_type="short", difficulty="medium", marks=4,
             ca="SQL: structured, ACID-compliant, relational (e.g., banking). NoSQL: flexible schema, horizontally scalable (e.g., social media feeds)."),
        dict(text="Analyze the trade-offs between using an array versus a linked list for implementing a queue.",
             q_type="short", difficulty="medium", marks=4,
             ca="Array: O(1) access but costly insertion/deletion at front. Linked list: O(1) enqueue/dequeue but higher memory overhead per node."),
        dict(text="Examine the memory usage and performance differences between pass-by-value and pass-by-reference in programming languages.",
             q_type="short", difficulty="hard", marks=4,
             ca="Pass-by-value copies the data (safe but memory-intensive for large objects). Pass-by-reference passes the address (efficient but risks unintended mutation)."),
        dict(text="Analyze the security vulnerabilities in the following login code snippet and explain how each can be exploited:\n\nquery = 'SELECT * FROM users WHERE username=\"' + username + '\" AND password=\"' + password + '\"'",
             q_type="long", difficulty="hard", marks=10,
             ca="The code is vulnerable to SQL injection. An attacker could input: admin'-- which closes the string and comments out the password check. Fix: use parameterised queries / prepared statements."),
        dict(text="Analyse the time and space complexity of QuickSort in the best, average, and worst cases. Explain what causes the worst case and how it can be avoided.",
             q_type="long", difficulty="hard", marks=10,
             ca="Best/Avg: O(n log n) time, O(log n) space. Worst: O(n²) time when pivot is always the smallest/largest (sorted array). Avoided by random pivot selection or median-of-three."),
    ],

    # ── 5. EVALUATE ───────────────────────────────────────────────────────────
    "evaluate": [
        dict(text="Which argument best justifies using microservices over a monolithic architecture for a large-scale e-commerce platform?",
             q_type="mcq", difficulty="hard", marks=2,
             oa="Microservices are always faster",
             ob="Microservices allow independent scaling and deployment of services",
             oc="Microservices eliminate all bugs",
             od="Monoliths cannot handle any database operations",
             ca="Microservices allow independent scaling and deployment of services"),
        dict(text="A team must choose between REST and GraphQL for a new API. Which criterion is MOST relevant to that decision?",
             q_type="mcq", difficulty="hard", marks=2,
             oa="Number of developers on the team",
             ob="Whether clients need flexible, precise data fetching",
             oc="The colour scheme of the front-end",
             od="The age of the server hardware",
             ca="Whether clients need flexible, precise data fetching"),
        dict(text="Evaluate whether blockchain is a suitable technology for a hospital's patient records system. Which factor is the strongest argument against its use?",
             q_type="mcq", difficulty="hard", marks=2,
             oa="Blockchain cannot store text",
             ob="Blockchain data is immutable, making corrections to records difficult",
             oc="Blockchain requires the internet",
             od="Blockchain was designed only for cryptocurrency",
             ca="Blockchain data is immutable, making corrections to records difficult"),
        dict(text="Which testing strategy provides the highest confidence that individual components integrate correctly?",
             q_type="mcq", difficulty="medium", marks=1,
             oa="Unit Testing", ob="Integration Testing",
             oc="Stress Testing", od="Regression Testing",
             ca="Integration Testing"),
        dict(text="Evaluate the suitability of Python vs C++ for developing a real-time embedded control system. Justify your recommendation.",
             q_type="short", difficulty="hard", marks=5,
             ca="C++ is more suitable: it compiles to native machine code, offers deterministic memory management, and has minimal runtime overhead — critical for real-time constraints. Python's interpreter overhead and garbage collector make timing unpredictable."),
        dict(text="Critically evaluate the use of cookies versus JWT tokens for session management in a web application.",
             q_type="short", difficulty="hard", marks=5,
             ca="Cookies: stateful, vulnerable to CSRF but easily invalidated. JWT: stateless, scalable, but revocation is complex. JWTs are preferred for distributed systems; cookies for simpler server-side session control."),
        dict(text="Assess the effectiveness of agile methodology compared to the waterfall model for software development in a startup environment.",
             q_type="short", difficulty="medium", marks=4,
             ca="Agile is more effective for startups due to iterative delivery, flexibility to change requirements, and continuous client feedback. Waterfall suits fixed-scope projects with well-defined requirements."),
        dict(text="Evaluate two different approaches to handling concurrency in web servers: multi-threading and event-loop (async IO). Recommend one for a high-traffic API.",
             q_type="short", difficulty="hard", marks=5,
             ca="Event-loop (async IO) is recommended for high-traffic APIs: lower memory overhead (one thread handles thousands of connections), no GIL issues in Python's async model. Multi-threading suits CPU-bound tasks."),
        dict(text="Evaluate the ethical implications of using facial recognition technology in public surveillance systems. Consider privacy, accuracy bias, and legal frameworks in your answer.",
             q_type="long", difficulty="hard", marks=10,
             ca="Covers: invasion of privacy, algorithmic bias against minority groups, lack of consent, GDPR/legal concerns, potential for misuse by authoritarian regimes, and recommendations for regulation."),
        dict(text="A company must decide between building its own data centre or migrating to cloud infrastructure (AWS/Azure). Evaluate both options considering cost, scalability, security, and maintenance. Provide a justified recommendation.",
             q_type="long", difficulty="hard", marks=10,
             ca="Cloud: lower upfront cost, elastic scalability, shared security responsibility, reduced maintenance. Own DC: higher control, potentially cheaper long-term at scale, data sovereignty. Recommendation depends on workload predictability and compliance needs."),
    ],

    # ── 6. CREATE ─────────────────────────────────────────────────────────────
    "create": [
        dict(text="You are designing a URL shortener service (like bit.ly). Which data structure is MOST appropriate for the core mapping?",
             q_type="mcq", difficulty="medium", marks=2,
             oa="Binary Search Tree",
             ob="Hash Map",
             oc="Doubly Linked List",
             od="Min Heap",
             ca="Hash Map"),
        dict(text="Which architectural pattern is best suited to designing a system where different components react to published events without tight coupling?",
             q_type="mcq", difficulty="hard", marks=2,
             oa="MVC (Model-View-Controller)",
             ob="Event-Driven Architecture",
             oc="Layered Architecture",
             od="Pipe-and-Filter",
             ca="Event-Driven Architecture"),
        dict(text="When designing a REST API for a blogging platform, which HTTP method and endpoint best represents creating a new post?",
             q_type="mcq", difficulty="easy", marks=1,
             oa="GET /posts",
             ob="PUT /posts",
             oc="POST /posts",
             od="DELETE /posts/new",
             ca="POST /posts"),
        dict(text="Which SOLID principle states that a class should have only one reason to change?",
             q_type="mcq", difficulty="medium", marks=1,
             oa="Open/Closed Principle",
             ob="Liskov Substitution",
             oc="Single Responsibility Principle",
             od="Dependency Inversion",
             ca="Single Responsibility Principle"),
        dict(text="Design a simple class diagram for a Library Management System. Include at least three classes with their attributes and relationships.",
             q_type="short", difficulty="medium", marks=5,
             ca="Classes: Book (isbn, title, author), Member (memberId, name, email), Loan (loanId, borrowDate, returnDate). Relationships: Member borrows Book through Loan (many-to-many resolved)."),
        dict(text="Propose a database schema for an online food delivery application. List your tables and their primary/foreign keys.",
             q_type="short", difficulty="hard", marks=5,
             ca="Tables: Users(userId PK), Restaurants(restaurantId PK), MenuItems(itemId PK, restaurantId FK), Orders(orderId PK, userId FK), OrderItems(orderId FK, itemId FK), Deliveries(deliveryId PK, orderId FK)."),
        dict(text="Create a Python generator function that yields Fibonacci numbers up to a given limit n.",
             q_type="short", difficulty="medium", marks=4,
             ca="def fib(n):\n    a, b = 0, 1\n    while a <= n:\n        yield a\n        a, b = b, a + b"),
        dict(text="Outline the architecture of a scalable chat application that supports 1 million concurrent users. Identify the key components and technologies.",
             q_type="short", difficulty="hard", marks=5,
             ca="WebSocket servers behind a load balancer, Redis pub/sub for message fanout, Kafka for async message persistence, PostgreSQL for history, CDN for static assets, horizontal scaling of stateless chat servers."),
        dict(text="Design and implement a complete REST API endpoint in Python (Flask) for a 'Task Manager' that supports CRUD operations. Include request validation and appropriate HTTP status codes.",
             q_type="long", difficulty="hard", marks=15,
             ca="Implement GET /tasks, POST /tasks, GET /tasks/<id>, PUT /tasks/<id>, DELETE /tasks/<id> using Flask with JSON request/response, 201 for creation, 404 for not found, 400 for bad request."),
        dict(text="Formulate a complete software development plan for a university examination management system. Include requirements gathering, system design, technology stack selection, testing strategy, and deployment plan.",
             q_type="long", difficulty="hard", marks=15,
             ca="Requirements: functional (schedule exams, assign rooms, generate seating) and non-functional (security, scalability). Design: ER diagram, use-case diagram. Stack: React, Node.js/Flask, PostgreSQL. Testing: unit, integration, UAT. Deployment: Docker + cloud."),
    ],
}


def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    total = 0
    for level, questions in QUESTIONS.items():
        for q in questions:
            ins(cur,
                text=q["text"],
                q_type=q["q_type"],
                blooms=level,
                difficulty=q["difficulty"],
                marks=q["marks"],
                oa=q.get("oa"),
                ob=q.get("ob"),
                oc=q.get("oc"),
                od=q.get("od"),
                ca=q.get("ca"))
            total += 1

    con.commit()
    con.close()
    print(f"Done. Inserted {total} questions ({total // 6} per Bloom's level).")


if __name__ == "__main__":
    main()
