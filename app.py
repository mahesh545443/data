import streamlit as st
import json
import os
import time
from groq import Groq
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from PIL import Image
from pypdf import PdfReader, PdfWriter
import io

# ==========================================
# API KEY
# ==========================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ==========================================
# SPACING & MARGINS
# ==========================================
SPACING = {
    'section_gap': 18,
    'heading_gap': 10,
    'bullet_gap': 5,
    'paragraph_gap': 12,
    'table_row_gap': 4,
}

MARGINS = {
    'left': 50, 'right': 50,
    'top': 15,  'bottom': 50,
    'page_border': 10,
}

# ==========================================
# CAREER TABLE DATA
# ==========================================
CAREER_TEMPLATES = {
    "Finance": [
        ["Finance Analytics", "Financial Data Analyst",
         "Improve profitability, forecasting accuracy, and cost control using financial data",
         "SQL, Excel, Python, Statistics, ML, GenAI, Financial Modeling",
         "JP Morgan, HDFC Bank, American Express, Barclays"],
        ["Finance Analytics", "Risk & Financial Planning Analyst",
         "Predict financial risks, detect anomalies, and strengthen budgeting & planning",
         "SQL, Python, Forecasting, Statistics, ML, GenAI",
         "KPMG, EY, Deloitte, PwC"]
    ],
    "Healthcare": [
        ["Healthcare Analytics", "Healthcare Data Analyst",
         "Analyze patient and hospital data to improve outcomes, efficiency, and care quality",
         "SQL, Python, Statistics, ML, GenAI, Healthcare Data",
         "Apollo Hospitals, Fortis, Practo, Narayana Health"],
        ["Healthcare Analytics", "Clinical Risk & Outcomes Analyst",
         "Predict patient risks, track treatment effectiveness, and optimize resource utilization",
         "SQL, Python, Statistics, ML, GenAI",
         "GE Healthcare, Philips, Medtronic"]
    ],
    "E-Commerce": [
        ["E-Commerce Analytics", "E-Commerce Data Analyst",
         "Optimize sales, pricing, and conversion using customer and product data",
         "SQL, Python, Statistics, ML, GenAI",
         "Amazon, Flipkart, Meesho, Nykaa"],
        ["E-Commerce Analytics", "Customer & Growth Analyst",
         "Analyze customer behavior, churn, and campaign performance to drive growth",
         "SQL, Python, Statistics, ML, GenAI",
         "Myntra, Swiggy, Zomato"]
    ],
    "Supply Chain": [
        ["Supply Chain Analytics", "Supply Chain Data Analyst",
         "Forecast demand and optimize inventory, logistics, and procurement efficiency",
         "SQL, Python, Statistics, ML, GenAI",
         "Amazon, DHL, Flipkart, Delhivery"]
    ],
    "Automobile": [
        ["Automobile Analytics", "Automotive Data Analyst",
         "Analyze vehicle, sensor, and production data to improve quality and efficiency",
         "SQL, Python, Statistics, ML, GenAI, IoT / Telematics Data",
         "Tata Motors, Mahindra, Hyundai, Maruti Suzuki"],
        ["Automobile Analytics", "Manufacturing Operations Analyst",
         "Reduce defects, downtime, and production bottlenecks using analytics",
         "SQL, Python, Time Series, ML, GenAI",
         "Bosch, Continental, TVS Motor, Ashok Leyland"]
    ],
    "Manufacturing": [
        ["Manufacturing Analytics", "Manufacturing Data Analyst",
         "Optimize production output, quality, and operational costs",
         "SQL, Python, Statistics, ML, GenAI, Process Data",
         "Siemens, ABB, GE, Schneider Electric"]
    ],
    "Retail": [
        ["Retail Analytics", "Retail Data Analyst",
         "Optimize inventory, sales forecasting, and customer insights",
         "SQL, Python, Statistics, ML, GenAI",
         "Reliance Retail, DMart, Big Bazaar, Spencer's"]
    ],
    "HR Analytics": [
        ["HR Analytics", "HR Data Analyst",
         "Analyze workforce trends, attrition patterns, and recruitment effectiveness",
         "SQL, Python, Statistics, ML, GenAI",
         "Deloitte, Accenture, IBM, Wipro"]
    ],
    "Cyber Security": [
        ["Cyber Security Analytics", "Security Data Analyst",
         "Detect threats, analyze patterns, and strengthen security posture",
         "SQL, Python, ML, GenAI, SIEM Tools",
         "Cisco, Palo Alto, CrowdStrike, Fortinet"]
    ]
}

# ==========================================
# AI PRESCRIPTION GENERATOR
# ==========================================
def get_ai_prescription_text(selected_domains):
    domain_str = " & ".join(selected_domains)
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        return {"error": "API Key not configured"}

    PROMPT = f"""You are a Senior Data Scientist at Analytics Avenue.
Generate a JSON prescription for: {domain_str}

CRITICAL RULES:
1. Use <b>text</b> for bold formatting on domain names, technologies
2. Return ONLY these keys:
   - "intro_line": Introduction with <b> tags
   - "domain_bullets": List of domain descriptions with <b> tags (one bullet per domain)
   - "projects_bullet": Projects description with <b> tags
   - "final_sentence": Closing with <b> tags

NOW GENERATE for: {domain_str}
Return ONLY valid JSON."""

    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": PROMPT}],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        data = json.loads(completion.choices[0].message.content)
        data["domains_title"] = domain_str
        return data
    except Exception as e:
        return {"error": str(e)}

def get_table_data_with_rowspan(selected_domains):
    table_rows = []
    domain_rowspan_map = {}
    for domain in selected_domains:
        if domain in CAREER_TEMPLATES:
            domain_rows = CAREER_TEMPLATES[domain]
            domain_rowspan_map[domain] = len(domain_rows)
            table_rows.extend(domain_rows)
    return table_rows, domain_rowspan_map

# ==========================================
# PDF HELPERS (unchanged)
# ==========================================
def draw_outer_border(c, page_width, page_height):
    margin = MARGINS['page_border']
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.rect(margin, margin, page_width - 2*margin, page_height - 2*margin, stroke=1, fill=0)

def draw_header_no_line(c, page_width, page_height):
    header_path = "assets/header.png"
    if not os.path.exists(header_path):
        c.setFillColor(colors.red)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, page_height - 50, "ERROR: header.png not found!")
        return 100
    try:
        img = Image.open(header_path)
        img_width, img_height = img.size
        aspect_ratio = img_width / img_height
        header_height = 100
        header_width = header_height * aspect_ratio
        if header_width > page_width:
            header_width = page_width
            header_height = header_width / aspect_ratio
        x_pos = (page_width - header_width) / 2
        y_pos = page_height - header_height - 10
        c.drawImage(header_path, x_pos, y_pos, width=header_width, height=header_height,
                    preserveAspectRatio=True, mask='auto')
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.line(MARGINS['left'], y_pos - 5, page_width - MARGINS['right'], y_pos - 5)
        return header_height + 30
    except:
        return 100

def create_page1(c, name, status, ai_content):
    page_width, page_height = A4
    L = MARGINS['left']
    R = page_width - MARGINS['right']
    W = R - L
    draw_outer_border(c, page_width, page_height)
    header_space = draw_header_no_line(c, page_width, page_height)
    y = page_height - header_space - 15

    style_normal = ParagraphStyle('Normal', fontName='Times-Roman', fontSize=11, leading=13, alignment=TA_LEFT)
    style_bullet = ParagraphStyle('Bullet', parent=style_normal, leftIndent=7, firstLineIndent=-7, leading=13)

    c.setFillColor(colors.black)
    c.setFont('Times-Bold', 11)
    c.drawString(L, y, f"Hi {name},")
    y -= 14

    p = Paragraph("Our Senior Data Scientist <b>Mr. Subramani</b>, has shared with you the prescription based on your recent consultation to join our <b>Nationwide Data Analytics Training and Placement Program 2025</b>.", style_normal)
    _, h = p.wrap(W, 120); p.drawOn(c, L, y - h); y -= h
    y -= 12

    c.setFont('Times-Bold', 11); c.drawString(L, y, "About Us"); y -= 14
    p = Paragraph("At <b>Analytics Avenue and Advanced Analytics</b>, we are a team of <b>Data Scientists, Data Engineers, and BI Developers</b> throughout India across various MNCs joined together to keep a pause for unemployment and empowered <b>500+ professionals</b> in the past year, enabling them to transition into various <b>Data Analytics roles</b>.", style_normal)
    _, h = p.wrap(W, 160); p.drawOn(c, L, y - h); y -= h
    y -= 12

    p_instr = Paragraph("<b>Below you can find the career road map, Key outcomes & suggestions given by our Data Scientist</b>", style_normal)
    _, h = p_instr.wrap(W, 100); p_instr.drawOn(c, L, y - h); y -= (h + 10)

    details = [
        ("Name", name), ("Status", status),
        ("Technologies Needed", "SQL, Python, Statistics, Power BI, Machine Learning, Gen AI"),
        ("Sectors Covered", ai_content.get('domains_title', ''))
    ]
    COLON_X = L + 140; VALUE_X = COLON_X + 15
    for label, value in details:
        c.setFont('Times-Bold', 11); c.drawString(L, y - 10, label); c.drawString(COLON_X, y - 10, ":")
        p_val = Paragraph(value, style_normal)
        _, vh = p_val.wrap(R - VALUE_X, 120); p_val.drawOn(c, VALUE_X, y - vh); y -= (vh + 4)

    y -= 12; c.setFont('Times-Bold', 11); c.drawString(L, y, "Career Roadmap"); y -= 14
    for step in ["Step 1 → Learn Tools (SQL, Python, Statistics, Power BI, Machine Learning, Gen AI)", "Step 2 → Domain-Specific Projects", "Step 3 → Role Readiness (interviews, placement support)"]:
        p_step = Paragraph(step, style_normal); _, h = p_step.wrap(W, 100); p_step.drawOn(c, L, y - h); y -= (h + 3)

    y -= 12; c.setFont('Times-Bold', 11); c.drawString(L, y, "Key Outcomes"); y -= 14
    for item in ["Data Analysis Skills (SQL, Python, Visualization, Statistics)", "Data Engineer Skills (Cloud, SQL, Python, Data Warehousing, ETL orchestration)", "Machine Learning & Gen AI (LLMs, Prompt Engineering, RAG Pipelines, Embeddings, Vector Databases, Fine-Tuning & Deployment)", f"Domain Knowledge ({ai_content.get('domains_title', '')} etc.)", "Recreate Industrial Standard projects worked by our Data Scientists", "Placement opportunities, Organic job calls and referral drives"]:
        p = Paragraph(f"• {item}", style_bullet); _, h = p.wrap(W, 300); p.drawOn(c, L, y - h); y -= (h + 3)

    y -= 12; c.setFont('Times-Bold', 11); c.drawString(L, y, "Prescription:"); y -= 14
    p = Paragraph(ai_content.get('intro_line', ''), style_normal); _, h = p.wrap(W, 140); p.drawOn(c, L, y - h); y -= (h + 8)
    for b_text in ai_content.get('domain_bullets', []):
        if b_text.strip():
            p = Paragraph(f"• {b_text}", style_bullet); _, h = p.wrap(W, 360); p.drawOn(c, L, y - h); y -= (h + 3)
    if ai_content.get('projects_bullet'):
        p = Paragraph(f"• {ai_content['projects_bullet']}", style_bullet); _, h = p.wrap(W, 360); p.drawOn(c, L, y - h); y -= (h + 8)
    if ai_content.get('final_sentence'):
        p_final = Paragraph(ai_content['final_sentence'], style_normal); _, fh = p_final.wrap(W, 140); p_final.drawOn(c, L, y - fh)

def create_page2(c, ai_content, table_rows, domain_rowspan_map):
    page_width, page_height = A4
    draw_outer_border(c, page_width, page_height)
    header_space = draw_header_no_line(c, page_width, page_height)
    L = MARGINS['left']; R = page_width - MARGINS['right']; W = R - L
    y = page_height - header_space - 15

    style_small = ParagraphStyle('Small', fontName='Times-Roman', fontSize=11, leading=13, alignment=TA_LEFT)
    style_heading = ParagraphStyle('Heading', fontName='Times-Bold', fontSize=11, leading=13, alignment=TA_LEFT)

    c.setFillColor(colors.black)
    c.setFont('Times-Bold', 11); c.drawString(L, y, "Our Customized Services for you:"); y -= 14

    services_data = [
        [Paragraph("<b>Service</b>", style_heading), Paragraph("<b>Details</b>", style_heading)],
        [Paragraph("<b>1. Industry-Relevant Projects</b>", style_heading), Paragraph(f"Work on 3 projects across {ai_content['domains_title']}, focusing on data modeling, EDA, Machine Learning, and GenAI for forecasting, cost optimization, anomaly detection, and decision support.", style_small)],
        [Paragraph("<b>2. Secret Job Portals Access</b>", style_heading), Paragraph("Setup and optimize your profile on 9 exclusive job portals to help you receive organic job calls", style_small)],
        [Paragraph("<b>3. Interview Preparation Materials</b>", style_heading), Paragraph("Lifetime access to interview notes, preparation guides, and materials prepared by top Data Scientists in real interview scenarios", style_small)],
        [Paragraph("<b>4. Monthly In-Person Training</b>", style_heading), Paragraph("Attend monthly in-house classroom sessions (1 weekend per month) for revision, rapid preparation, and mentorship from experienced professionals", style_small)]
    ]
    services_table = Table(services_data, colWidths=[W * 0.32, W * 0.68])
    services_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    services_table.wrapOn(c, W, page_height)
    services_h = services_table._height
    services_table.drawOn(c, L, y - services_h)
    y -= (services_h + 20)

    y -= 12; c.setFont("Times-Bold", 11); c.drawString(L, y, f"{ai_content['domains_title']} – Career Prescription Table"); y -= 14

    headers = ["Domain", "Role", "Exciting Challenge", "Key Technical Skills", "Targeted Companies"]
    career_data = [[Paragraph(f"<b>{h}</b>", style_heading) for h in headers]]
    current_row = 1; processed_domains = {}
    for row in table_rows:
        domain = row[0]
        if domain not in processed_domains:
            processed_domains[domain] = current_row
            career_data.append([Paragraph(f"<b>{domain}</b>", style_small), Paragraph(str(row[1]), style_small), Paragraph(str(row[2]), style_small), Paragraph(str(row[3]), style_small), Paragraph(str(row[4]), style_small)])
        else:
            career_data.append(["", Paragraph(str(row[1]), style_small), Paragraph(str(row[2]), style_small), Paragraph(str(row[3]), style_small), Paragraph(str(row[4]), style_small)])
        current_row += 1

    col_widths = [W*0.18, W*0.15, W*0.25, W*0.20, W*0.22]
    career_table = Table(career_data, colWidths=col_widths, repeatRows=1)
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.white), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8), ('NOSPLIT', (0, 0), (-1, -1)),
        ('BOX', (0, 0), (-1, -1), 1, colors.black), ('INNERGRID', (1, 0), (-1, -1), 1, colors.black),
        ('LINEAFTER', (0, 0), (0, -1), 1, colors.black), ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
    ]
    for domain, start_row in processed_domains.items():
        rowspan = domain_rowspan_map.get(domain, 1)
        if rowspan > 1:
            table_style.append(('SPAN', (0, start_row), (0, start_row + rowspan - 1)))
            for sub_row in range(start_row, start_row + rowspan - 1):
                table_style.append(('LINEBELOW', (1, sub_row), (-1, sub_row), 1, colors.black))
        table_style.append(('LINEBELOW', (0, start_row + rowspan - 1), (-1, start_row + rowspan - 1), 1, colors.black))
    career_table.setStyle(TableStyle(table_style))
    career_table.wrapOn(c, W, page_height)
    career_h = career_table._height
    career_table.drawOn(c, L, y - career_h)
    y -= (career_h + 15)

    reveal_text = "Actual projects will be revealed during placement training"
    box_width = W; box_height = 30
    if y - box_height < MARGINS['bottom']:
        y = MARGINS['bottom'] + box_height + 5
    c.setStrokeColor(colors.black); c.setLineWidth(1)
    c.rect(L, y - box_height, box_width, box_height, stroke=1, fill=0)
    c.setFont("Times-Bold", 11)
    text_width = c.stringWidth(reveal_text, "Times-Bold", 11)
    c.drawString(L + (box_width - text_width) / 2, y - (box_height / 2) - 4, reveal_text)

def create_final_pdf(name, status, ai_content, table_rows, domain_rowspan_map, output_path):
    buffer1 = io.BytesIO()
    c1 = canvas.Canvas(buffer1, pagesize=A4)
    create_page1(c1, name, status, ai_content); c1.save(); buffer1.seek(0)

    buffer2 = io.BytesIO()
    c2 = canvas.Canvas(buffer2, pagesize=A4)
    create_page2(c2, ai_content, table_rows, domain_rowspan_map); c2.save(); buffer2.seek(0)

    buffer3 = io.BytesIO()
    c3 = canvas.Canvas(buffer3, pagesize=A4)
    draw_outer_border(c3, A4[0], A4[1]); c3.save(); buffer3.seek(0)

    writer = PdfWriter()
    writer.add_page(PdfReader(buffer1).pages[0])
    writer.add_page(PdfReader(buffer2).pages[0])

    template_path = "assets/template.pdf"
    if os.path.exists(template_path):
        template_reader = PdfReader(template_path)
        if len(template_reader.pages) >= 3:
            page3_template = template_reader.pages[2]
            border_reader = PdfReader(buffer3)
            page3_template.merge_page(border_reader.pages[0])
            writer.add_page(page3_template)

    with open(output_path, 'wb') as f:
        writer.write(f)
    return True, None

# ==========================================
# STREAMLIT UI — 3 TAB DESIGN
# ==========================================
st.set_page_config(page_title="AI Prescription Generator", layout="centered")

# ── Custom CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Lato', sans-serif;
}

/* Hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 780px; }

/* ── Logo header ── */
.aa-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 18px 0 10px 0;
    border-bottom: 2px solid #e8e8e8;
    margin-bottom: 6px;
}
.aa-header img { height: 52px; }
.aa-header .aa-name {
    color: #064b86;
    font-size: 22px;
    font-weight: 700;
    line-height: 1.25;
}

/* ── Tab bar ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0px;
    border-bottom: 2px solid #e0e0e0;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Lato', sans-serif;
    font-size: 15px;
    font-weight: 600;
    color: #666;
    padding: 10px 28px;
    border: none;
    border-bottom: 3px solid transparent;
    background: transparent;
    margin-bottom: -2px;
    transition: color 0.2s, border-color 0.2s;
}
.stTabs [aria-selected="true"] {
    color: #c0392b !important;
    border-bottom: 3px solid #c0392b !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab"]:hover { color: #c0392b; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 24px; }

/* ── Section headings inside tabs ── */
.tab-section-title {
    font-size: 13px;
    font-weight: 700;
    color: #999;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    margin-bottom: 16px;
    margin-top: 8px;
    padding-bottom: 6px;
    border-bottom: 1px solid #f0f0f0;
}

/* ── Info card (used in Important Attributes) ── */
.info-card {
    background: #f8f9fb;
    border: 1px solid #e8eaf0;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 14px;
}
.info-card .label {
    font-size: 11px;
    font-weight: 700;
    color: #aaa;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 4px;
}
.info-card .value {
    font-size: 15px;
    font-weight: 600;
    color: #1a1a1a;
}

/* ── Roadmap steps ── */
.roadmap-step {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 12px 0;
    border-bottom: 1px solid #f3f3f3;
}
.roadmap-step:last-child { border-bottom: none; }
.step-badge {
    min-width: 28px; height: 28px;
    background: #064b86;
    color: white;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 700;
    flex-shrink: 0; margin-top: 1px;
}
.step-text { font-size: 14px; color: #333; line-height: 1.5; }

/* ── Outcome bullets ── */
.outcome-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 9px 0;
    border-bottom: 1px solid #f3f3f3;
    font-size: 14px;
    color: #333;
    line-height: 1.5;
}
.outcome-dot {
    min-width: 7px; height: 7px;
    background: #c0392b;
    border-radius: 50%;
    margin-top: 6px; flex-shrink: 0;
}

/* ── Career table styling ── */
.career-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }
.career-table th {
    background: #064b86; color: white;
    padding: 9px 10px; text-align: left;
    font-weight: 700; font-size: 12px;
}
.career-table td {
    padding: 9px 10px;
    border-bottom: 1px solid #e8e8e8;
    vertical-align: top;
    color: #333;
}
.career-table tr:nth-child(even) td { background: #f8f9fb; }
.career-table tr:hover td { background: #eef3fb; }
.domain-cell {
    font-weight: 700; color: #064b86;
    background: #eef3fb !important;
}

/* ── AI prescription box ── */
.prescription-box {
    background: #f8f9fb;
    border-left: 4px solid #064b86;
    border-radius: 0 10px 10px 0;
    padding: 18px 20px;
    margin-bottom: 16px;
    font-size: 14px;
    line-height: 1.7;
    color: #222;
}
.bullet-item {
    display: flex; gap: 10px;
    padding: 8px 0;
    font-size: 14px; line-height: 1.6; color: #333;
    border-bottom: 1px solid #f0f0f0;
}
.bullet-item:last-child { border-bottom: none; }
.bullet-icon { color: #c0392b; font-weight: 700; flex-shrink: 0; }

/* ── Generate button ── */
div.stButton > button {
    background: #064b86;
    color: white;
    font-weight: 700;
    font-size: 15px;
    border: none;
    border-radius: 8px;
    padding: 12px 28px;
    width: 100%;
    transition: background 0.2s;
}
div.stButton > button:hover { background: #0a5fa3; }

/* ── Download button ── */
div.stDownloadButton > button {
    background: #c0392b;
    color: white;
    font-weight: 700;
    font-size: 15px;
    border: none;
    border-radius: 8px;
    padding: 12px 28px;
    width: 100%;
}
div.stDownloadButton > button:hover { background: #e74c3c; }

/* ── Inputs ── */
.stTextInput input, .stSelectbox select {
    border-radius: 8px;
    border: 1.5px solid #dde1ea;
    font-size: 14px;
}
.stMultiSelect { border-radius: 8px; }

/* ── Status badge ── */
.status-badge {
    display: inline-block;
    background: #eef3fb;
    color: #064b86;
    font-size: 12px;
    font-weight: 700;
    padding: 3px 12px;
    border-radius: 20px;
    border: 1px solid #c4d7f0;
    margin-bottom: 12px;
}

/* ── Final sentence box ── */
.final-box {
    background: #fff8e1;
    border: 1px solid #f0c040;
    border-radius: 8px;
    padding: 14px 18px;
    font-size: 14px;
    color: #333;
    line-height: 1.6;
    margin-top: 12px;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────
logo_url = "https://raw.githubusercontent.com/Analytics-Avenue/streamlit-dataapp/main/logo.png"
st.markdown(f"""
<div class="aa-header">
    <img src="{logo_url}">
    <div class="aa-name">Analytics Avenue &<br>Advanced Analytics</div>
</div>
""", unsafe_allow_html=True)

# ── Asset check ────────────────────────────────────────────────────────────
header_ok   = os.path.exists("assets/header.png")
template_ok = os.path.exists("assets/template.pdf")
if not (header_ok and template_ok):
    st.error("❌ Missing required assets!")
    st.write(f"{'✅' if header_ok else '❌'} assets/header.png")
    st.write(f"{'✅' if template_ok else '❌'} assets/template.pdf")
    st.stop()

# ── Session state ──────────────────────────────────────────────────────────
if "ai_content"         not in st.session_state: st.session_state.ai_content         = None
if "table_rows"         not in st.session_state: st.session_state.table_rows         = None
if "domain_rowspan_map" not in st.session_state: st.session_state.domain_rowspan_map = None
if "pdf_path"           not in st.session_state: st.session_state.pdf_path           = None
if "submitted_name"     not in st.session_state: st.session_state.submitted_name     = ""
if "submitted_status"   not in st.session_state: st.session_state.submitted_status   = ""
if "submitted_domains"  not in st.session_state: st.session_state.submitted_domains  = []

# ── 3 TABS ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Overview", "Important Attributes", "Application"])

# ══════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW  (input form)
# ══════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="tab-section-title">Candidate Details</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name", placeholder="e.g. Arun Kumar", key="name_input")
    with col2:
        status = st.selectbox("Current Status", ["Working Professional", "Student", "Job Seeker"], key="status_input")

    st.markdown('<div class="tab-section-title" style="margin-top:20px;">Target Domains</div>', unsafe_allow_html=True)
    domains = st.multiselect(
        "Select 1–3 domains you want to specialise in",
        ["Finance", "Supply Chain", "Healthcare", "HR Analytics", "E-Commerce",
         "Automobile", "Manufacturing", "Retail", "Cyber Security"],
        key="domains_input"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 Generate Prescription", key="gen_btn"):
        errors = []
        if not name:    errors.append("Name is required")
        if not domains: errors.append("Select at least one domain")
        if errors:
            for e in errors:
                st.error(f"❌ {e}")
        else:
            with st.spinner("🤖 AI is writing your prescription…"):
                ai_content = get_ai_prescription_text(domains)

            if "error" in ai_content:
                st.error(f"AI Error: {ai_content['error']}")
            else:
                table_rows, domain_rowspan_map = get_table_data_with_rowspan(domains)

                with st.spinner("📄 Building PDF…"):
                    ts        = int(time.time())
                    safe_name = "".join([ch for ch in name if ch.isalnum() or ch in (' ', '_')]).rstrip()
                    filename  = f"Prescription_{safe_name.replace(' ', '_')}_{ts}.pdf"
                    os.makedirs("output", exist_ok=True)
                    output_path = f"output/{filename}"
                    create_final_pdf(name, status, ai_content, table_rows, domain_rowspan_map, output_path)

                # Save to session
                st.session_state.ai_content         = ai_content
                st.session_state.table_rows         = table_rows
                st.session_state.domain_rowspan_map = domain_rowspan_map
                st.session_state.pdf_path           = output_path
                st.session_state.submitted_name     = name
                st.session_state.submitted_status   = status
                st.session_state.submitted_domains  = domains

                st.success("✅ Prescription generated! See **Important Attributes** and **Application** tabs.")

# ══════════════════════════════════════════════════════════════
# TAB 2 — IMPORTANT ATTRIBUTES
# ══════════════════════════════════════════════════════════════
with tab2:
    if not st.session_state.ai_content:
        st.info("💡 Fill in the **Overview** tab and click Generate to see attributes here.")
    else:
        ai   = st.session_state.ai_content
        name = st.session_state.submitted_name
        stat = st.session_state.submitted_status

        # ── Candidate summary cards ──
        st.markdown('<div class="tab-section-title">Candidate Summary</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="info-card"><div class="label">Name</div><div class="value">{name}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="info-card"><div class="label">Status</div><div class="value">{stat}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="info-card"><div class="label">Domains</div><div class="value">{ai.get("domains_title","")}</div></div>', unsafe_allow_html=True)

        # ── Technologies ──
        st.markdown('<div class="tab-section-title" style="margin-top:24px;">Technologies You Will Learn</div>', unsafe_allow_html=True)
        tech_list = ["SQL", "Python", "Statistics", "Power BI", "Machine Learning", "Gen AI"]
        cols = st.columns(len(tech_list))
        for i, tech in enumerate(tech_list):
            cols[i].markdown(f'<div style="text-align:center; background:#eef3fb; border:1px solid #c4d7f0; border-radius:8px; padding:10px 4px; font-size:13px; font-weight:700; color:#064b86;">{tech}</div>', unsafe_allow_html=True)

        # ── Career Roadmap ──
        st.markdown('<div class="tab-section-title" style="margin-top:24px;">Career Roadmap</div>', unsafe_allow_html=True)
        roadmap = [
            ("1", "Learn Tools", "SQL, Python, Statistics, Power BI, Machine Learning, Gen AI"),
            ("2", "Domain Projects", "Work on real industry-standard projects in your chosen domains"),
            ("3", "Role Readiness",  "Interview prep, placement support, and referral drives"),
        ]
        for num, title, desc in roadmap:
            st.markdown(f"""
            <div class="roadmap-step">
                <div class="step-badge">{num}</div>
                <div class="step-text"><strong>{title}</strong><br><span style="color:#777;font-size:13px;">{desc}</span></div>
            </div>""", unsafe_allow_html=True)

        # ── Key Outcomes ──
        st.markdown('<div class="tab-section-title" style="margin-top:24px;">Key Outcomes</div>', unsafe_allow_html=True)
        outcomes = [
            "Data Analysis Skills — SQL, Python, Visualization, Statistics",
            "Data Engineer Skills — Cloud, SQL, Python, Data Warehousing, ETL orchestration",
            "Machine Learning & Gen AI — LLMs, Prompt Engineering, RAG Pipelines, Embeddings, Vector Databases, Fine-Tuning & Deployment",
            f"Domain Knowledge — {ai.get('domains_title','')} and related industries",
            "Recreate industrial-standard projects built by our Data Scientists",
            "Placement opportunities, organic job calls, and referral drives",
        ]
        for item in outcomes:
            st.markdown(f'<div class="outcome-item"><div class="outcome-dot"></div><div>{item}</div></div>', unsafe_allow_html=True)

        # ── Career Table ──
        st.markdown('<div class="tab-section-title" style="margin-top:24px;">Career Prescription Table</div>', unsafe_allow_html=True)
        table_rows = st.session_state.table_rows
        drm        = st.session_state.domain_rowspan_map

        html_table = """
        <div style="overflow-x:auto;">
        <table class="career-table">
            <thead>
                <tr>
                    <th>Domain</th><th>Role</th><th>Exciting Challenge</th>
                    <th>Key Skills</th><th>Target Companies</th>
                </tr>
            </thead><tbody>"""

        prev_domain = None
        for row in table_rows:
            domain = row[0]
            domain_cell = ""
            if domain != prev_domain:
                rowspan = drm.get(domain, 1)
                domain_cell = f'<td rowspan="{rowspan}" class="domain-cell">{domain}</td>'
                prev_domain = domain
            html_table += f"""
            <tr>
                {domain_cell}
                <td><strong>{row[1]}</strong></td>
                <td>{row[2]}</td>
                <td><span style="color:#064b86;">{row[3]}</span></td>
                <td>{row[4]}</td>
            </tr>"""

        html_table += "</tbody></table></div>"
        st.markdown(html_table, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# TAB 3 — APPLICATION  (AI prescription + download)
# ══════════════════════════════════════════════════════════════
with tab3:
    if not st.session_state.ai_content:
        st.info("💡 Fill in the **Overview** tab and click Generate to see the prescription here.")
    else:
        ai   = st.session_state.ai_content
        name = st.session_state.submitted_name

        # ── Greeting ──
        st.markdown('<div class="tab-section-title">AI-Generated Prescription</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="status-badge">Prepared for {name}</div>', unsafe_allow_html=True)

        # Intro line
        intro = ai.get("intro_line", "")
        if intro:
            clean_intro = intro.replace("<b>", "**").replace("</b>", "**")
            st.markdown(f'<div class="prescription-box">{intro}</div>', unsafe_allow_html=True)

        # Domain bullets
        bullets = ai.get("domain_bullets", [])
        if bullets:
            st.markdown('<div class="tab-section-title" style="margin-top:20px;">Domain Breakdown</div>', unsafe_allow_html=True)
            for b in bullets:
                st.markdown(f'<div class="bullet-item"><div class="bullet-icon">▸</div><div>{b}</div></div>', unsafe_allow_html=True)

        # Projects bullet
        proj = ai.get("projects_bullet", "")
        if proj:
            st.markdown('<div class="tab-section-title" style="margin-top:20px;">Hands-On Projects</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="bullet-item"><div class="bullet-icon">▸</div><div>{proj}</div></div>', unsafe_allow_html=True)

        # Final sentence
        final = ai.get("final_sentence", "")
        if final:
            st.markdown(f'<div class="final-box">📌 {final}</div>', unsafe_allow_html=True)

        # ── Services ──
        st.markdown('<div class="tab-section-title" style="margin-top:28px;">Customised Services</div>', unsafe_allow_html=True)
        services = [
            ("🏭", "Industry-Relevant Projects",      f"3 real projects across {ai.get('domains_title','')} — covering EDA, ML, and GenAI."),
            ("🔐", "Secret Job Portals Access",        "Profile setup on 9 exclusive portals for organic job calls."),
            ("📚", "Interview Preparation Materials",  "Lifetime access to notes & guides from top Data Scientists."),
            ("🏫", "Monthly In-Person Training",       "Weekend classroom sessions for revision & mentorship."),
        ]
        for icon, svc, detail in services:
            st.markdown(f"""
            <div class="info-card" style="display:flex; gap:14px; align-items:flex-start;">
                <div style="font-size:22px;">{icon}</div>
                <div><strong style="font-size:14px;">{svc}</strong><br>
                <span style="font-size:13px; color:#666;">{detail}</span></div>
            </div>""", unsafe_allow_html=True)

        # ── Download ──
        st.markdown('<div class="tab-section-title" style="margin-top:28px;">Download Prescription</div>', unsafe_allow_html=True)
        pdf_path = st.session_state.pdf_path
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "⬇️ Download Full PDF Prescription",
                    f,
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            st.warning("PDF not found. Please regenerate.")
