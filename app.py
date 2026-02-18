import streamlit as st
import json
import os
import time
from groq import Groq
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from PIL import Image
from pypdf import PdfReader, PdfWriter
import io

# ==========================================
# API KEY - SET YOUR GROQ API KEY HERE
# ==========================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
  

# ==========================================
# UNIFORM SPACING FOR ENTIRE PDF
# ==========================================
SPACING = {
    'section_gap': 18,        # Gap between all major sections
    'heading_gap': 10,        # Gap from heading to content
    'bullet_gap': 5,          # Gap between bullets
    'paragraph_gap': 12,      # Gap between paragraphs
    'table_row_gap': 4,       # Gap between table rows
}

MARGINS = {
    'left': 50,
    'right': 50,
    'top': 15,
    'bottom': 50,
    'page_border': 10,
}

# ==========================================
# COMPLETE CAREER TABLE DATA
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
    """Generate prescription using Groq AI"""
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

EXAMPLES:

For "Finance & Supply Chain":
{{
  "intro_line": "Given your background, we will support your transition into <b>Finance & Supply Chain Analytics</b> roles, enabling you to solve real business and operational problems using <b>Machine Learning and GenAI</b>.",
  "domain_bullets": [
    "In <b>Finance Analytics</b>, you will work on financial performance analysis, budgeting and forecasting, risk assessment, fraud pattern identification, and profitability optimization.",
    "In <b>Supply Chain Analytics</b>, you will focus on demand forecasting, inventory optimization, logistics performance, supplier analysis, and end-to-end cost efficiency."
  ],
  "projects_bullet": "Hands-on projects include financial variance and profitability analysis, risk and anomaly detection, demand forecasting, inventory health analysis, logistics optimization, and supplier performance tracking. You will also leverage <b>GenAI</b> for automated insights, root-cause analysis, and conversational analytics (projects revealed during placement training).",
  "final_sentence": "You will apply <b>SQL, Statistics, Machine Learning, and GenAI</b> to <b>finance and supply chain</b> datasets, preparing you for high-impact analytics roles across these domains."
}}

For "Healthcare & Finance":
{{
  "intro_line": "Given your background, we will support your transition into <b>Healthcare and Finance Analytics</b> roles, equipping you to solve both operational and business challenges using <b>Machine Learning and GenAI</b>.",
  "domain_bullets": [
    "In <b>Healthcare Analytics</b>, you will focus on patient data analysis, clinical outcome monitoring, resource utilization optimization, risk prediction, and treatment effectiveness assessment.",
    "In <b>Finance Analytics</b>, you will work on financial performance analysis, budgeting and forecasting, risk assessment, fraud detection support, and profitability modeling."
  ],
  "projects_bullet": "Hands-on projects include patient risk prediction, clinical trend analysis, healthcare operations insights, financial variance analysis, profitability modeling, risk assessment frameworks, and fraud pattern detection. You will also use <b>GenAI</b> for automated insights, root-cause analysis, and conversational analytics (actual projects revealed during placement training).",
  "final_sentence": "You will apply <b>SQL, Statistics, Machine Learning, and GenAI</b> to extract insights from <b>healthcare systems and financial datasets</b>, preparing you for high-impact analytics roles across these domains."
}}

For "E-Commerce & Supply Chain":
{{
  "intro_line": "Given your background, we will support your transition into <b>E-Commerce and Supply Chain Analytics</b> roles, enabling you to solve customer engagement and operational challenges using <b>Machine Learning and GenAI</b>.",
  "domain_bullets": [
    "In <b>E-Commerce Analytics</b>, you will focus on sales optimization, customer behavior analysis, conversion rate improvement, pricing strategies, and campaign effectiveness tracking.",
    "In <b>Supply Chain Analytics</b>, you will work on demand forecasting, inventory optimization, logistics efficiency, procurement analysis, and end-to-end supply chain visibility."
  ],
  "projects_bullet": "Hands-on projects include sales forecasting, customer segmentation, conversion funnel analysis, demand planning, inventory optimization, logistics performance tracking, and supplier evaluation. You will also leverage <b>GenAI</b> for automated insights, predictive analytics, and conversational dashboards (projects revealed during placement training).",
  "final_sentence": "You will apply <b>SQL, Statistics, Machine Learning, and GenAI</b> to <b>e-commerce platforms and supply chain systems</b>, preparing you for high-impact analytics roles across these domains."
}}

NOW GENERATE for: {domain_str}
Match the style above with proper <b> tags. Return ONLY valid JSON."""

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
    """Build career table with rowspan"""
    table_rows = []
    domain_rowspan_map = {}
    
    for domain in selected_domains:
        if domain in CAREER_TEMPLATES:
            domain_rows = CAREER_TEMPLATES[domain]
            domain_rowspan_map[domain] = len(domain_rows)
            table_rows.extend(domain_rows)
    
    return table_rows, domain_rowspan_map

# ==========================================
# PDF HELPER FUNCTIONS
# ==========================================
def draw_outer_border(c, page_width, page_height):
    """Draw outer border on all pages"""
    margin = MARGINS['page_border']
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.rect(margin, margin, page_width - 2*margin, page_height - 2*margin, stroke=1, fill=0)

def draw_header_no_line(c, page_width, page_height):
    """Draw header with line"""
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
        
        # Line below header
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.line(MARGINS['left'], y_pos - 5, page_width - MARGINS['right'], y_pos - 5)
        
        return header_height + 30
       
    except Exception as e:
        return 100

# ==========================================
# PAGE 1 - UNIFORM SPACING
# ==========================================
def create_page1(c, name, status, ai_content):
    page_width, page_height = A4

    L = MARGINS['left']
    R = page_width - MARGINS['right']
    W = R - L

    draw_outer_border(c, page_width, page_height)
    header_space = draw_header_no_line(c, page_width, page_height)
    
    # Starting position
    y = page_height - header_space - 15 

    # Styles
    style_normal = ParagraphStyle(
        'Normal',
        fontName='Times-Roman',
        fontSize=11,
        leading=13, 
        alignment=TA_LEFT
    )

    style_bullet = ParagraphStyle(
        'Bullet',
        parent=style_normal,
        leftIndent=7,
        firstLineIndent=-7,
        leading=13
    )

    c.setFillColor(colors.black)

    # GREETING
    c.setFont('Times-Bold', 11)
    c.drawString(L, y, f"Hi {name},")
    y -= 14

    # INTRO
    intro_text = (
        "Our Senior Data Scientist <b>Mr. Subramani</b>, has shared with you the "
        "prescription based on your recent consultation to join our "
        "<b>Nationwide Data Analytics Training and Placement Program 2025</b>."
    )
    p = Paragraph(intro_text, style_normal)
    _, h = p.wrap(W, 120)
    p.drawOn(c, L, y - h)
    y -= h 

    # --- UNIFORM GAP BEFORE ABOUT US ---
    y -= 12 
    c.setFont('Times-Bold', 11)
    c.drawString(L, y, "About Us")
    y -= 14 
    
    about_text = (
        "At <b>Analytics Avenue and Advanced Analytics</b>, we are a team of "
        "<b>Data Scientists, Data Engineers, and BI Developers</b> throughout India "
        "across various MNCs joined together to keep a pause for unemployment and "
        "empowered <b>500+ professionals</b> in the past year, enabling them to "
        "transition into various <b>Data Analytics roles</b>."
    )
    p = Paragraph(about_text, style_normal)
    _, h = p.wrap(W, 160)
    p.drawOn(c, L, y - h)
    y -= h

    # --- GAP BEFORE INSTRUCTION ---
    y -= 12
    instr_text = "Below you can find the career road map, Key outcomes & suggestions given by our Data Scientist"
    p_instr = Paragraph(f"<b>{instr_text}</b>", style_normal)
    _, h = p_instr.wrap(W, 100)
    p_instr.drawOn(c, L, y - h)
    y -= (h + 10)

    # DETAILS TABLE
    details = [
        ("Name", name),
        ("Status", status),
        ("Technologies Needed", "SQL, Python, Statistics, Power BI, Machine Learning, Gen AI"),
        ("Sectors Covered", ai_content.get('domains_title', 'Finance & Supply Chain'))
    ]

    COLON_X = L + 140
    VALUE_X = COLON_X + 15

    for label, value in details:
        c.setFont('Times-Bold', 11)
        c.drawString(L, y - 10, label)
        c.drawString(COLON_X, y - 10, ":")
        p_val = Paragraph(value, style_normal)
        _, vh = p_val.wrap(R - VALUE_X, 120)
        p_val.drawOn(c, VALUE_X, y - vh)
        y -= (vh + 4)

    # --- UNIFORM GAP BEFORE CAREER ROADMAP ---
    y -= 12
    c.setFont('Times-Bold', 11)
    c.drawString(L, y, "Career Roadmap")
    y -= 14 
    
    roadmap = [
        "Step 1 → Learn Tools (SQL, Python, Statistics, Power BI, Machine Learning, Gen AI)",
        "Step 2 → Domain-Specific Projects",
        "Step 3 → Role Readiness (interviews, placement support)"
    ]

    for step in roadmap:
        p_step = Paragraph(step, style_normal)
        _, h = p_step.wrap(W, 100)
        p_step.drawOn(c, L, y - h)
        y -= (h + 3)

    # --- UNIFORM GAP BEFORE KEY OUTCOMES ---
    y -= 12
    c.setFont('Times-Bold', 11)
    c.drawString(L, y, "Key Outcomes")
    y -= 14 
    
    outcomes = [
        "Data Analysis Skills (SQL, Python, Visualization, Statistics)",
        "Data Engineer Skills (Cloud, SQL, Python, Data Warehousing, ETL orchestration)",
        "Machine Learning & Gen AI (LLMs, Prompt Engineering, RAG Pipelines, Embeddings, Vector Databases, Fine-Tuning & Deployment)",
        f"Domain Knowledge ({ai_content.get('domains_title', 'Finance & Supply Chain')} etc.)",
        "Recreate Industrial Standard projects worked by our Data Scientists",
        "Placement opportunities, Organic job calls and referral drives"
    ]

    for item in outcomes:
        p = Paragraph(f"• {item}", style_bullet)
        _, h = p.wrap(W, 300)
        p.drawOn(c, L, y - h)
        y -= (h + 3)

    # --- UNIFORM GAP  FORE PRESCRIPTION ---
    y -= 12
    c.setFont('Times-Bold', 11)
    c.drawString(L, y, "Prescription:")
    y -= 14 
    
    intro_line = ai_content.get('intro_line', "Given your background...")
    p = Paragraph(intro_line, style_normal)
    _, h = p.wrap(W, 140)
    p.drawOn(c, L, y - h)
    y -= (h + 8)

    for b_text in ai_content.get('domain_bullets', []):
        if b_text.strip():
            p = Paragraph(f"• {b_text}", style_bullet)
            _, h = p.wrap(W, 360)
            p.drawOn(c, L, y - h)
            y -= (h + 3)

    projects_bullet = ai_content.get('projects_bullet')
    if projects_bullet:
        p = Paragraph(f"• {projects_bullet}", style_bullet)
        _, h = p.wrap(W, 360)
        p.drawOn(c, L, y - h)
        y -= (h + 8)

    # --- FINAL SENTENCE (FIXED) ---
    final_sentence = ai_content.get(
        'final_sentence', 
        "You will apply SQL, Statistics, Machine Learning, and GenAI to finance and supply chain datasets."
    )
    if final_sentence:
        p_final = Paragraph(final_sentence, style_normal)
        _, fh = p_final.wrap(W, 140)
        p_final.drawOn(c, L, y - fh)
        y -= fh

# ==========================================
# PAGE 2 - MATCHING PAGE 1 STYLE
# ==========================================
def create_page2(c, ai_content, table_rows, domain_rowspan_map):
    """Page 2 with exact same font, size, and spacing as Page 1"""
    page_width, page_height = A4
    
    draw_outer_border(c, page_width, page_height)
    header_space = draw_header_no_line(c, page_width, page_height)
    
    L = MARGINS['left']
    R = page_width - MARGINS['right']
    W = R - L
    
    # Starting Y position (consistent with Page 1)
    y = page_height - header_space - 15 
    
    # Styles - UPDATED TO TIMES-ROMAN 11pt (Matches Page 1)
    style_small = ParagraphStyle(
        'Small',
        fontName='Times-Roman',
        fontSize=11,
        leading=13,
        alignment=TA_LEFT # Changed to Left to match general document style
    )
    
    style_heading = ParagraphStyle(
        'Heading',
        fontName='Times-Bold',
        fontSize=11,
        leading=13,
        alignment=TA_LEFT
    )
    
    c.setFillColor(colors.black)

    # 1. SERVICES TABLE HEADING
    c.setFont('Times-Bold', 11)
    c.drawString(L, y, "Our Customized Services for you:")
    y -= 14 # Standardized Gap below heading
    
    services_data = [
        [Paragraph("<b>Service</b>", style_heading), Paragraph("<b>Details</b>", style_heading)],
        [Paragraph("<b>1. Industry-Relevant Projects</b>", style_heading), 
         Paragraph(f"Work on 3 projects across {ai_content['domains_title']}, focusing on data modeling, EDA, Machine Learning, and GenAI for forecasting, cost optimization, anomaly detection, and decision support.", style_small)],
        [Paragraph("<b>2. Secret Job Portals Access</b>", style_heading),
         Paragraph("Setup and optimize your profile on 9 exclusive job portals to help you receive organic job calls", style_small)],
        [Paragraph("<b>3. Interview Preparation Materials</b>", style_heading),
         Paragraph("Lifetime access to interview notes, preparation guides, and materials prepared by top Data Scientists in real interview scenarios", style_small)],
        [Paragraph("<b>4. Monthly In-Person Training</b>", style_heading),
         Paragraph("Attend monthly in-house classroom sessions (1 weekend per month) for revision, rapid preparation, and mentorship from experienced professionals", style_small)]
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
    
    # Move Y down after table
    y -= (services_h + 20)
    
    # 2. CAREER TABLE HEADING
    y -= 12 # Uniform Gap before new section
    c.setFont("Times-Bold", 11)
    c.drawString(L, y, f"{ai_content['domains_title']} – Career Prescription Table")
    y -= 14 # Standardized Gap below heading
    
    headers = ["Domain", "Role", "Exciting Challenge", "Key Technical Skills", "Targeted Companies"]
    career_data = [[Paragraph(f"<b>{h}</b>", style_heading) for h in headers]]
    
    current_row = 1
    processed_domains = {}
    
    for row in table_rows:
        domain = row[0]
        if domain not in processed_domains:
            processed_domains[domain] = current_row
            career_data.append([
                Paragraph(f"<b>{domain}</b>", style_small),
                Paragraph(str(row[1]), style_small),
                Paragraph(str(row[2]), style_small),
                Paragraph(str(row[3]), style_small),
                Paragraph(str(row[4]), style_small)
            ])
        else:
            career_data.append([
                "",
                Paragraph(str(row[1]), style_small),
                Paragraph(str(row[2]), style_small),
                Paragraph(str(row[3]), style_small),
                Paragraph(str(row[4]), style_small)
            ])
        current_row += 1
    
    col_widths = [W * 0.18, W * 0.15, W * 0.25, W * 0.20, W * 0.22]
    career_table = Table(career_data, colWidths=col_widths, repeatRows=1)
    
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'), # Left align to match text
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('NOSPLIT', (0, 0), (-1, -1)),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (1, 0), (-1, -1), 1, colors.black),
        ('LINEAFTER', (0, 0), (0, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
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
    
    # 3. REVEAL BOX - UPDATED TO TIMES-BOLD
    reveal_text = "Actual projects will be revealed during placement training"
    box_width = W
    box_height = 30
    
    # Check if box fits, otherwise nudge up
    if y - box_height < MARGINS['bottom']:
        y = MARGINS['bottom'] + box_height + 5

    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.rect(L, y - box_height, box_width, box_height, stroke=1, fill=0)
    
    c.setFont("Times-Bold", 11)
    text_width = c.stringWidth(reveal_text, "Times-Bold", 11)
    text_x = L + (box_width - text_width) / 2
    text_y = y - (box_height / 2) - 4
    c.drawString(text_x, text_y, reveal_text)

# ==========================================
# PDF GENERATION
# ==========================================
def create_final_pdf(name, status, ai_content, table_rows, domain_rowspan_map, output_path):
    """Generate complete PDF"""
    
    buffer1 = io.BytesIO()
    c1 = canvas.Canvas(buffer1, pagesize=A4)
    create_page1(c1, name, status, ai_content)
    c1.save()
    buffer1.seek(0)
    
    buffer2 = io.BytesIO()
    c2 = canvas.Canvas(buffer2, pagesize=A4)
    create_page2(c2, ai_content, table_rows, domain_rowspan_map)
    c2.save()
    buffer2.seek(0)
    
    buffer3 = io.BytesIO()
    c3 = canvas.Canvas(buffer3, pagesize=A4)
    draw_outer_border(c3, A4[0], A4[1])
    c3.save()
    buffer3.seek(0)
    
    writer = PdfWriter()
    
    reader1 = PdfReader(buffer1)
    writer.add_page(reader1.pages[0])
    
    reader2 = PdfReader(buffer2)
    writer.add_page(reader2.pages[0])
    
    template_path = "assets/template.pdf"
    if os.path.exists(template_path):
        template_reader = PdfReader(template_path)
        if len(template_reader.pages) >= 3:
            page3_template = template_reader.pages[2]
            
            if page3_template.mediabox.width != A4[0] or page3_template.mediabox.height != A4[1]:
                page3_template.scale_to(A4[0], A4[1])
            
            border_reader = PdfReader(buffer3)
            page3_border = border_reader.pages[0]
            page3_template.merge_page(page3_border)
            writer.add_page(page3_template)
    
    with open(output_path, 'wb') as f:
        writer.write(f)
    
    return True, None

# STREAMLIT UI
# ==========================================
st.set_page_config(page_title="Analytics Avenue Generator", layout="wide")

# Global CSS - Bold, Left-aligned, Production UI
st.markdown("""
<style>
    /* Import bold production font */
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    /* Remove default padding */
    .block-container {
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }

    /* Header brand area */
    .brand-header {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 28px 0 12px 0;
        border-bottom: 4px solid #064b86;
        margin-bottom: 32px;
    }

    .brand-text-top {
        font-family: 'Syne', sans-serif;
        font-size: 42px;
        font-weight: 800;
        color: #064b86;
        line-height: 1.1;
        letter-spacing: -1px;
    }

    .brand-text-sub {
        font-family: 'Syne', sans-serif;
        font-size: 22px;
        font-weight: 700;
        color: #1a7ed4;
        letter-spacing: 0.5px;
    }

    /* Page title */
    h1 {
        font-family: 'Syne', sans-serif !important;
        font-size: 48px !important;
        font-weight: 800 !important;
        color: #0a0a0a !important;
        letter-spacing: -1.5px !important;
        margin-bottom: 6px !important;
    }

    /* Section labels */
    .stTextInput label,
    .stSelectbox label,
    .stMultiSelect label {
        font-size: 16px !important;
        font-weight: 700 !important;
        color: #0a0a0a !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    /* Input fields */
    .stTextInput input,
    .stSelectbox select {
        font-size: 17px !important;
        font-weight: 600 !important;
        padding: 12px 16px !important;
        border: 2px solid #d0d7de !important;
        border-radius: 8px !important;
    }

    /* Submit button */
    .stFormSubmitButton button {
        background: #064b86 !important;
        color: white !important;
        font-family: 'Syne', sans-serif !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        padding: 16px 32px !important;
        border-radius: 8px !important;
        border: none !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        transition: background 0.2s !important;
    }

    .stFormSubmitButton button:hover {
        background: #043a6a !important;
    }

    /* Download button */
    .stDownloadButton button {
        background: #12a150 !important;
        color: white !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        padding: 14px 28px !important;
        border-radius: 8px !important;
        border: none !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
    }

    /* Error / success alerts */
    .stAlert {
        font-size: 16px !important;
        font-weight: 700 !important;
    }

    /* Expander headers */
    .streamlit-expanderHeader {
        font-size: 18px !important;
        font-weight: 700 !important;
        color: #064b86 !important;
    }

    /* Divider accent */
    .section-title {
        font-family: 'Syne', sans-serif;
        font-size: 22px;
        font-weight: 800;
        color: #064b86;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin: 28px 0 12px 0;
        padding-left: 12px;
        border-left: 5px solid #064b86;
    }

    /* Form card background */
    section[data-testid="stForm"] {
        background: #f4f7fb;
        border-radius: 12px;
        padding: 28px 32px !important;
        border: 1.5px solid #dce4ef;
    }
</style>
""", unsafe_allow_html=True)

# ── BRAND HEADER ──────────────────────────────────────────
logo_url = "https://raw.githubusercontent.com/Analytics-Avenue/streamlit-dataapp/main/logo.png"
st.markdown(f"""
<div class="brand-header">
    <img src="{logo_url}" width="64" style="border-radius:10px;">
    <div>
        <div class="brand-text-top">Analytics Avenue</div>
        <div class="brand-text-sub">Advanced Analytics Division</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.title("🤖 AI Prescription Generator")
st.markdown('<p style="font-size:18px; font-weight:600; color:#444; margin-top:-10px; margin-bottom:28px;">Generate a personalised data career prescription powered by AI</p>', unsafe_allow_html=True)

# ── ASSET CHECK ───────────────────────────────────────────
header_ok = os.path.exists("assets/header.png")
template_ok = os.path.exists("assets/template.pdf")
if not (header_ok and template_ok):
    st.error("❌ Missing required assets!")
    st.write(f"{'✅' if header_ok else '❌'} header.png")
    st.write(f"{'✅' if template_ok else '❌'} template.pdf")
    st.stop()

# ── FORM ──────────────────────────────────────────────────
st.markdown('<div class="section-title">Your Details</div>', unsafe_allow_html=True)

with st.form("form"):
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        name = st.text_input("Name *", placeholder="e.g. Student Name")

    with col2:
        status = st.selectbox("Status *", ["Working Professional", "Student", "Job Seeker"])

    domains = st.multiselect(
        "Target Domains *",
        ["Finance", "Supply Chain", "Healthcare", "HR Analytics", "E-Commerce",
         "Automobile", "Manufacturing", "Retail", "Cyber Security"],
        help="Select 1–3 domains that best match your career goals"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    submit = st.form_submit_button("🚀 Generate My Prescription", use_container_width=True)

# ── SUBMIT LOGIC ──────────────────────────────────────────
if submit:
    errors = []
    if not name:
        errors.append("❌ Name is required")
    if not domains:
        errors.append("❌ Select at least one domain")

    if errors:
        for e in errors:
            st.error(e)
    else:
        with st.spinner("🤖 AI generating your prescription..."):
            ai_content = get_ai_prescription_text(domains)

        if "error" in ai_content:
            st.error(f"AI Error: {ai_content['error']}")
        else:
            with st.spinner("📊 Building career table..."):
                table_rows, domain_rowspan_map = get_table_data_with_rowspan(domains)

            with st.spinner("📄 Creating PDF..."):
                ts = int(time.time())
                safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '_')]).rstrip()
                filename = f"Prescription_{safe_name.replace(' ', '_')}_{ts}.pdf"
                output_path = f"output/{filename}"
                os.makedirs("output", exist_ok=True)

                success, error_msg = create_final_pdf(
                    name, status, ai_content, table_rows, domain_rowspan_map, output_path
                )

            if success:
                st.success("✅ Prescription Generated Successfully!")

                with open(output_path, "rb") as f:
                    st.download_button(
                        "⬇️ Download Your PDF",
                        f,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )

                with st.expander("📋 View AI Content"):
                    st.json(ai_content)

                with st.expander("📊 View Career Data"):
                    st.write(f"**Roles generated:** {len(table_rows)}")
                    st.write(f"**Domains:** {domain_rowspan_map}")
            else:
                st.error(f"PDF Error: {error_msg}")

