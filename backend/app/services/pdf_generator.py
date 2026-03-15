from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO
from datetime import datetime

def generate_paper_pdf(paper_data):
    """
    Generates a professional PDF version of a question paper.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=12,
        alignment=1,  # Center
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        fontName='Helvetica'
    )
    
    question_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceBefore=12,
        spaceAfter=6,
        leading=14,
        fontName='Helvetica'
    )
    
    option_style = ParagraphStyle(
        'OptionStyle',
        parent=styles['Normal'],
        fontSize=10,
        leftIndent=20,
        spaceBefore=2,
        fontName='Helvetica'
    )

    story = []

    # Paper Title
    story.append(Paragraph(paper_data['title'], title_style))
    story.append(Spacer(1, 12))

    # Header section (Marks / Time / Date)
    header_data = [
        [f"Subject: {paper_data.get('subject_name', 'Examination')}", ""],
        [f"Total Marks: {paper_data['total_marks']}", f"Duration: {paper_data['duration_minutes']} minutes"],
        [f"Date: {datetime.now().strftime('%d %B %Y')}", ""]
    ]
    
    header_table = Table(header_data, colWidths=[300, 190])
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # Separator
    story.append(Table([[""]], colWidths=[490], rowHeights=[1], style=[('LINEBELOW', (0,0), (-1,-1), 1, colors.black)]))
    story.append(Spacer(1, 20))

    # Questions
    # Check if questions exist
    questions = paper_data.get('questions', [])
    if not questions:
        story.append(Paragraph("No questions available in this paper.", styles['Normal']))
    
    for i, q in enumerate(questions):
        # Question text with number and marks
        q_text = f"Q{i+1}. {q['text']} <font color='grey' size='9'>({q['marks']} pts)</font>"
        story.append(Paragraph(q_text, question_style))
        
        # Options if MCQ
        if q['question_type'] == 'mcq' and q.get('options'):
            opts = q['options']
            for key in ['a', 'b', 'c', 'd']:
                if opts.get(key):
                    story.append(Paragraph(f"{key.upper()}) {opts[key]}", option_style))
        
        story.append(Spacer(1, 8))

    doc.build(story)
    buffer.seek(0)
    return buffer
