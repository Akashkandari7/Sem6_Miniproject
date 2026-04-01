from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from io import BytesIO
from datetime import datetime


def generate_paper_pdf(paper_data):
    """
    Generates a professional university-style examination paper PDF.
    Includes: University header, course code, subject, duration, marks,
    instructions, and questions organized by section (MCQ / Short / Long).
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=35,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()
    page_width = A4[0] - 90  # usable width after margins

    # ── Custom Styles ──────────────────────────────────────────────

    university_style = ParagraphStyle(
        'UniversityStyle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=2,
        textColor=colors.HexColor('#1a1a2e'),
    )

    dept_style = ParagraphStyle(
        'DeptStyle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
        fontName='Helvetica',
        spaceAfter=2,
        textColor=colors.HexColor('#333333'),
    )

    exam_title_style = ParagraphStyle(
        'ExamTitleStyle',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceBefore=6,
        spaceAfter=4,
        textColor=colors.HexColor('#1a1a2e'),
    )

    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        fontName='Helvetica',
        textColor=colors.HexColor('#222222'),
    )

    meta_bold_style = ParagraphStyle(
        'MetaBoldStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#222222'),
    )

    section_heading_style = ParagraphStyle(
        'SectionHeadingStyle',
        parent=styles['Heading3'],
        fontSize=12,
        leading=15,
        fontName='Helvetica-Bold',
        spaceBefore=16,
        spaceAfter=8,
        textColor=colors.HexColor('#1a1a2e'),
        borderPadding=(0, 0, 4, 0),
    )

    instruction_style = ParagraphStyle(
        'InstructionStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        fontName='Helvetica',
        leftIndent=16,
        spaceBefore=2,
        textColor=colors.HexColor('#333333'),
    )

    instruction_heading_style = ParagraphStyle(
        'InstructionHeadingStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        fontName='Helvetica-Bold',
        spaceBefore=8,
        spaceAfter=4,
        textColor=colors.HexColor('#1a1a2e'),
    )

    question_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontSize=10.5,
        leading=14,
        fontName='Helvetica',
        spaceBefore=8,
        spaceAfter=4,
        textColor=colors.HexColor('#111111'),
    )

    option_style = ParagraphStyle(
        'OptionStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        leftIndent=28,
        spaceBefore=1,
        spaceAfter=1,
        fontName='Helvetica',
        textColor=colors.HexColor('#222222'),
    )

    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique',
        textColor=colors.HexColor('#888888'),
        spaceBefore=20,
    )

    story = []

    # ── Extract data ───────────────────────────────────────────────

    subject_name = paper_data.get('subject_name', 'Examination')
    subject_code = paper_data.get('subject_code', '')
    paper_title = paper_data.get('title', 'Question Paper')
    total_marks = paper_data.get('total_marks', 0)
    duration = paper_data.get('duration_minutes', 0)
    questions = paper_data.get('questions', [])
    date_str = datetime.now().strftime('%d %B %Y')

    # ── University Header Block ────────────────────────────────────

    story.append(Paragraph("UNIVERSITY OF TECHNOLOGY", university_style))
    story.append(Paragraph("Department of Computer Science &amp; Engineering", dept_style))
    story.append(Spacer(1, 4))

    # Decorative double line
    story.append(HRFlowable(
        width="100%", thickness=1.5,
        color=colors.HexColor('#1a1a2e'),
        spaceBefore=2, spaceAfter=0
    ))
    story.append(HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor('#1a1a2e'),
        spaceBefore=1, spaceAfter=6
    ))

    # Exam title
    story.append(Paragraph(paper_title.upper(), exam_title_style))
    story.append(Spacer(1, 4))

    # ── Meta Info Table (Subject, Code, Date, Marks, Duration) ────

    code_display = f"<b>Course Code:</b> {subject_code}" if subject_code else ""
    meta_data = [
        [
            Paragraph(f"<b>Subject:</b> {subject_name}", meta_style),
            Paragraph(code_display, meta_style),
        ],
        [
            Paragraph(f"<b>Date:</b> {date_str}", meta_style),
            Paragraph(f"<b>Max. Marks:</b> {total_marks}", meta_style),
        ],
        [
            Paragraph(f"<b>Duration:</b> {duration} Minutes", meta_style),
            Paragraph(f"<b>Total Questions:</b> {len(questions)}", meta_style),
        ],
    ]

    meta_table = Table(meta_data, colWidths=[page_width * 0.55, page_width * 0.45])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # ── Instructions Section ───────────────────────────────────────

    # Categorise questions
    mcq_qs = [q for q in questions if q.get('question_type') == 'mcq']
    short_qs = [q for q in questions if q.get('question_type') == 'short']
    long_qs = [q for q in questions if q.get('question_type') == 'long']

    instructions = [
        "All questions are compulsory unless stated otherwise.",
        f"This paper consists of <b>{len(questions)}</b> questions for a total of <b>{total_marks}</b> marks.",
    ]

    # Build section descriptions for instructions
    section_descs = []
    if mcq_qs:
        mcq_marks = sum(q['marks'] for q in mcq_qs)
        section_descs.append(
            f"Section A — <b>{len(mcq_qs)}</b> Multiple Choice Question(s) [{mcq_marks} Marks]"
        )
    if short_qs:
        short_marks = sum(q['marks'] for q in short_qs)
        section_descs.append(
            f"Section B — <b>{len(short_qs)}</b> Short Answer Question(s) [{short_marks} Marks]"
        )
    if long_qs:
        long_marks = sum(q['marks'] for q in long_qs)
        section_descs.append(
            f"Section C — <b>{len(long_qs)}</b> Long Answer Question(s) [{long_marks} Marks]"
        )

    if section_descs:
        instructions.append("The paper is divided into: " + "; ".join(section_descs) + ".")

    instructions.append("Write your answers clearly and legibly.")
    instructions.append("No electronic devices are allowed unless specified.")

    story.append(Paragraph("General Instructions:", instruction_heading_style))
    for idx, inst in enumerate(instructions, 1):
        story.append(Paragraph(f"{idx}. {inst}", instruction_style))

    story.append(Spacer(1, 6))
    story.append(HRFlowable(
        width="100%", thickness=0.75,
        color=colors.HexColor('#999999'),
        spaceBefore=4, spaceAfter=8
    ))

    # ── Render Questions by Section ────────────────────────────────

    q_number = 1  # global question counter

    def render_section(section_label, section_tag, qs, q_start):
        """Renders a group of questions as a labelled section."""
        if not qs:
            return q_start

        marks_total = sum(q['marks'] for q in qs)
        elements = []

        # Section heading
        elements.append(Paragraph(
            f"{section_label}  "
            f"<font size='9' color='#666666'>[{marks_total} Marks]</font>",
            section_heading_style,
        ))
        elements.append(HRFlowable(
            width="100%", thickness=0.5,
            color=colors.HexColor('#cccccc'),
            spaceBefore=0, spaceAfter=6
        ))

        num = q_start
        for q in qs:
            marks_label = f"[{q['marks']} Mark{'s' if q['marks'] != 1 else ''}]"
            q_text = (
                f"<b>Q{num}.</b> {q['text']}  "
                f"<font size='8.5' color='#666666'>{marks_label}</font>"
            )
            elements.append(Paragraph(q_text, question_style))

            # MCQ options
            if q.get('question_type') == 'mcq' and q.get('options'):
                opts = q['options']
                option_labels = ['a', 'b', 'c', 'd']
                # Render options in a 2-column grid for a cleaner look
                opt_rows = []
                for key in option_labels:
                    val = opts.get(key, '')
                    if val:
                        opt_rows.append(f"({key.upper()}) {val}")

                if len(opt_rows) == 4:
                    # 2x2 grid
                    opt_table_data = [
                        [
                            Paragraph(opt_rows[0], option_style),
                            Paragraph(opt_rows[1], option_style),
                        ],
                        [
                            Paragraph(opt_rows[2], option_style),
                            Paragraph(opt_rows[3], option_style),
                        ],
                    ]
                    opt_table = Table(opt_table_data, colWidths=[page_width * 0.48, page_width * 0.48])
                    opt_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                        ('LEFTPADDING', (0, 0), (-1, -1), 20),
                    ]))
                    elements.append(opt_table)
                else:
                    # Single column for fewer options
                    for row in opt_rows:
                        elements.append(Paragraph(row, option_style))

            elements.append(Spacer(1, 4))
            num += 1

        story.extend(elements)
        return num

    # Section A — MCQ
    if mcq_qs:
        q_number = render_section(
            "SECTION A — Multiple Choice Questions",
            "mcq", mcq_qs, q_number,
        )

    # Section B — Short Answer
    if short_qs:
        q_number = render_section(
            "SECTION B — Short Answer Questions",
            "short", short_qs, q_number,
        )

    # Section C — Long Answer
    if long_qs:
        q_number = render_section(
            "SECTION C — Long Answer Questions",
            "long", long_qs, q_number,
        )

    # If there are questions that don't match standard types
    other_qs = [q for q in questions if q.get('question_type') not in ('mcq', 'short', 'long')]
    if other_qs:
        q_number = render_section(
            "SECTION — General Questions",
            "other", other_qs, q_number,
        )

    # Edge case: no questions at all
    if not questions:
        story.append(Spacer(1, 24))
        story.append(Paragraph(
            "<i>No questions have been added to this paper yet.</i>",
            ParagraphStyle('EmptyNote', parent=styles['Normal'],
                           fontSize=11, alignment=TA_CENTER,
                           textColor=colors.HexColor('#888888'))
        ))

    # ── Footer ─────────────────────────────────────────────────────

    story.append(Spacer(1, 16))
    story.append(HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor('#cccccc'),
        spaceBefore=8, spaceAfter=4
    ))
    story.append(Paragraph("— End of Question Paper —", footer_style))

    # ── Build PDF ──────────────────────────────────────────────────

    doc.build(story)
    buffer.seek(0)
    return buffer
