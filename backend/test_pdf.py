import sys
import os
sys.path.insert(0, '/Users/niteshsharma/Desktop/minor-project-app/backend')
from app import create_app
from app.extensions import db
from app.models.paper import Paper
from app.models.subject import Subject
from app.models.user import User
from app.services.pdf_generator import generate_paper_pdf

app = create_app('development')
with app.app_context():
    # Fetch first paper
    paper = Paper.query.first()
    if not paper:
        print("No paper found. Going to create one...")
        subject = Subject.query.first()
        user = User.query.first()
        if not subject or not user:
            print("No subject/user. Exiting.")
            sys.exit(1)
            
        paper = Paper(
            title="Test Paper",
            total_marks=10,
            duration_minutes=30,
            config={},
            subject_id=subject.id,
            created_by=user.id
        )
        db.session.add(paper)
        db.session.commit()
    
    print(f"Paper Subject ID: {paper.subject_id}")
    print(f"Paper Subject object: {paper.subject}")
    if paper.subject:
        print(f"Subject Name: {paper.subject.name}")
    
    paper_data = paper.to_dict()
    paper_data['questions'] = [q.to_dict() for q in paper.questions]
    
    # EXACT CODE FROM papers.py:
    paper_data['subject_name'] = paper.subject.name if paper.subject else "Examination"
    print("paper_data['subject_name']:", paper_data['subject_name'])
    
    try:
        pdf_buffer = generate_paper_pdf(paper_data)
        with open("/tmp/test_paper.pdf", "wb") as f:
            f.write(pdf_buffer.getbuffer())
        print("PDF generated successfully at /tmp/test_paper.pdf")
    except Exception as e:
        print("Error generating PDF:", e)
