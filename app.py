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
# API KEY
# ==========================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ==========================================
# UNIFORM SPACING FOR ENTIRE PDF
# ==========================================
SPACING = {
    'section_gap': 18,
    'heading_gap': 10,
    'bullet_gap': 5,
    'paragraph_gap': 12,
    'table_row_gap': 4,
}

MARGINS = {
    'left': 50,
    'right': 50,
    'top': 15,
    'bottom': 50,
    'page_border': 10,
}

# ==========================================
# COMPLETE CAREER TABLE DATA — UNCHANGED
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
# AI PRESCRIPTION GENERATOR — UNCHANGED
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
    c.setStrokeColor(colors.black)
    c.setLineWidth(1.5)
    c.rect(15, 15, page_width - 30, page_height - 30, stroke=1, fill=0)

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
    except Exception as e:
        return 100


# ==========================================
# PAGE 1 — UNCHANGED
# ==========================================
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

    intro_text = (
        "Our Senior Data Scientist <b>Mr. Subramani</b>, has shared with you the "
        "prescription based on your recent consultation to join our "
        "<b>Nationwide Data Analytics Training and Placement Program 2025</b>."
    )
    p = Paragraph(intro_text, style_normal)
    _, h = p.wrap(W, 120)
    p.drawOn(c, L, y - h)
    y -= h

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

    y -= 12
    instr_text = "Below you can find the career road map, Key outcomes & suggestions given by our Data Scientist"
    p_instr = Paragraph(f"<b>{instr_text}</b>", style_normal)
    _, h = p_instr.wrap(W, 100)
    p_instr.drawOn(c, L, y - h)
    y -= (h + 10)

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

    y -= 12
    c.setFont('Times-Bold', 11)
    c.drawString(L, y, "Career Roadmap")
    y -= 14

    roadmap = [
        "Step 1 \u2192 Learn Tools (SQL, Python, Statistics, Power BI, Machine Learning, Gen AI)",
        "Step 2 \u2192 Domain-Specific Projects",
        "Step 3 \u2192 Role Readiness (interviews, placement support)"
    ]
    for step in roadmap:
        p_step = Paragraph(step, style_normal)
        _, h = p_step.wrap(W, 100)
        p_step.drawOn(c, L, y - h)
        y -= (h + 3)

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

    final_sentence = ai_content.get('final_sentence',
        "You will apply SQL, Statistics, Machine Learning, and GenAI to finance and supply chain datasets.")
    if final_sentence:
        p_final = Paragraph(final_sentence, style_normal)
        _, fh = p_final.wrap(W, 140)
        p_final.drawOn(c, L, y - fh)
        y -= fh


# ==========================================
# PAGE 2 — ALL 3 FIXES APPLIED
# ==========================================
def create_page2(c, ai_content, table_rows, domain_rowspan_map):
    page_width, page_height = A4
    draw_outer_border(c, page_width, page_height)
    header_space = draw_header_no_line(c, page_width, page_height)
    L = MARGINS['left']
    R = page_width - MARGINS['right']
    W = R - L
    y = page_height - header_space - 15

    style_small = ParagraphStyle('Small', fontName='Times-Roman', fontSize=11, leading=13, alignment=TA_LEFT)
    style_heading = ParagraphStyle('Heading', fontName='Times-Bold', fontSize=11, leading=13, alignment=TA_LEFT)

    c.setFillColor(colors.black)

    c.setFont('Times-Bold', 11)
    c.drawString(L, y, "Our Customized Services for you:")
    y -= 14

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
    y -= (services_h + 12)

    # FIX 1: Title bold + bracketed note on second line (italic), NO bottom box
    c.setFont("Times-Bold", 11)
    c.drawString(L, y, f"{ai_content['domains_title']} \u2013 Career Prescription Table")
    y -= 14
    c.setFont("Times-Italic", 11)
    c.drawString(L, y, "(Actual projects will be revealed during placement training)")
    y -= 14

    headers = ["Domain", "Role", "Exciting Challenge", "Key Technical Skills", "Targeted Companies"]
    career_data = [[Paragraph(f"<b>{h}</b>", style_heading) for h in headers]]

    # FIX 3: Build processed_domains and full_domain_rowspan from row[0] directly
    current_row = 1
    processed_domains = {}    # full domain name -> start row index in table
    full_domain_rowspan = {}  # full domain name -> row count

    for row in table_rows:
        full_domain = row[0]  # e.g. "Finance Analytics"
        if full_domain not in processed_domains:
            processed_domains[full_domain] = current_row
            full_domain_rowspan[full_domain] = 1
            career_data.append([
                Paragraph(f"<b>{full_domain}</b>", style_small),
                Paragraph(str(row[1]), style_small),
                Paragraph(str(row[2]), style_small),
                Paragraph(str(row[3]), style_small),
                Paragraph(str(row[4]), style_small)
            ])
        else:
            full_domain_rowspan[full_domain] += 1
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
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('INNERGRID', (1, 0), (-1, -1), 0.5, colors.black),
        ('LINEAFTER', (0, 0), (0, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]

    for full_domain, start_row in processed_domains.items():
        rowspan = full_domain_rowspan[full_domain]
        if rowspan > 1:
            # SPAN domain cell vertically across all its rows
            table_style.append(('SPAN', (0, start_row), (0, start_row + rowspan - 1)))
            table_style.append(('VALIGN', (0, start_row), (0, start_row + rowspan - 1), 'MIDDLE'))
            # Light grey thin line between rows of SAME domain (cols 1 onward only)
            for sub_row in range(start_row, start_row + rowspan - 1):
                table_style.append(('LINEBELOW', (1, sub_row), (-1, sub_row), 0.3, colors.lightgrey))
        # FIX 3: Thick black line ONLY after the LAST row of each domain group
        table_style.append(('LINEBELOW', (0, start_row + rowspan - 1), (-1, start_row + rowspan - 1), 1.5, colors.black))

    career_table.setStyle(TableStyle(table_style))
    career_table.wrapOn(c, W, page_height)
    career_h = career_table._height
    career_table.drawOn(c, L, y - career_h)
    # FIX 1: No bottom reveal box drawn here


# ==========================================
# PDF GENERATION
# ==========================================
def create_final_pdf(name, status, ai_content, table_rows, domain_rowspan_map, output_path):
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

    # FIX 2: No border buffer for page 3
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
            # FIX 2: No border merge on page 3
            writer.add_page(page3_template)

    with open(output_path, 'wb') as f:
        writer.write(f)

    return True, None


# ==========================================
# STREAMLIT UI
# ==========================================
st.set_page_config(page_title="Analytics Avenue Generator", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        max-width: 100% !important;
    }

    #MainMenu, footer, header { visibility: hidden; }

    .brand-wrap {
        display: flex;
        align-items: center;
        gap: 18px;
        margin-bottom: 28px;
    }
    .brand-name {
        font-size: 26px;
        font-weight: 800;
        color: #064b86;
        line-height: 1.3;
    }
    .divider {
        border: none;
        border-top: 2px solid #e0e0e0;
        margin: 0 0 32px 0;
    }

    h1 {
        font-size: 48px !important;
        font-weight: 900 !important;
        color: #0a0a0a !important;
        letter-spacing: -1px !important;
        line-height: 1.1 !important;
        margin-bottom: 6px !important;
    }

    .subtitle {
        font-size: 17px;
        font-weight: 500;
        color: #555;
        margin-bottom: 36px;
    }

    h2 {
        font-size: 30px !important;
        font-weight: 800 !important;
        color: #0a0a0a !important;
        margin-bottom: 16px !important;
    }
    h3 {
        font-size: 22px !important;
        font-weight: 700 !important;
        color: #0a0a0a !important;
        margin-bottom: 12px !important;
    }

    .card {
        background: #fff;
        border: 1.5px solid #e5e7eb;
        border-radius: 10px;
        padding: 24px 28px;
        margin-bottom: 20px;
    }
    .card-label {
        font-size: 13px;
        font-weight: 700;
        color: #064b86;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    .card-text {
        font-size: 16px;
        font-weight: 500;
        color: #222;
        line-height: 1.7;
    }
    .card ul {
        margin: 0;
        padding-left: 18px;
    }
    .card ul li {
        font-size: 15px;
        font-weight: 500;
        color: #333;
        margin-bottom: 6px;
        line-height: 1.6;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 32px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 16px !important;
        font-weight: 600 !important;
        color: #555 !important;
        padding: 12px 28px !important;
        border: none !important;
        background: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        color: #064b86 !important;
        font-weight: 800 !important;
        border-bottom: 3px solid #064b86 !important;
    }

    .stTextInput label,
    .stSelectbox label,
    .stMultiSelect label {
        font-size: 15px !important;
        font-weight: 700 !important;
        color: #0a0a0a !important;
        letter-spacing: 0.3px !important;
    }

    .stTextInput input {
        font-size: 16px !important;
        font-weight: 500 !important;
        padding: 12px 14px !important;
        border: 1.5px solid #d0d7de !important;
        border-radius: 6px !important;
        background: #fff !important;
    }

    .stFormSubmitButton > button {
        background-color: #064b86 !important;
        color: #fff !important;
        font-size: 17px !important;
        font-weight: 700 !important;
        padding: 14px 36px !important;
        border-radius: 6px !important;
        border: none !important;
        letter-spacing: 0.3px !important;
        margin-top: 12px !important;
        width: auto !important;
    }
    .stFormSubmitButton > button:hover {
        background-color: #053d70 !important;
    }

    .stDownloadButton > button {
        background-color: #1a7f37 !important;
        color: #fff !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        padding: 12px 28px !important;
        border-radius: 6px !important;
        border: none !important;
    }

    .stAlert p {
        font-size: 15px !important;
        font-weight: 600 !important;
    }

    .streamlit-expanderHeader p {
        font-size: 17px !important;
        font-weight: 700 !important;
        color: #0a0a0a !important;
    }
</style>
""", unsafe_allow_html=True)

# ── BRAND HEADER ─────────────────────────────────────────
logo_url = "https://raw.githubusercontent.com/Analytics-Avenue/streamlit-dataapp/main/logo.png"
st.markdown(f"""
<div class="brand-wrap">
    <img src="{logo_url}" width="64" style="border-radius:8px;">
    <div class="brand-name">
        Analytics Avenue &amp;<br>Advanced Analytics
    </div>
</div>
<hr class="divider">
""", unsafe_allow_html=True)

# ── PAGE TITLE ───────────────────────────────────────────
st.title("🤖 AI Prescription Generator")
st.markdown('<p class="subtitle">Generate a personalised data career prescription powered by AI</p>', unsafe_allow_html=True)

# ── TABS ─────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Overview", "Application"])

# ════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ════════════════════════════════════════════════════════
with tab1:
    st.header("Overview")

    st.markdown("""
    <div class="card">
        <div class="card-label">Purpose</div>
        <div class="card-text">
            Generate personalised, AI-powered career prescriptions for aspiring data professionals —
            combining Groq LLaMA 3.3 70B intelligence with domain-specific career templates to produce
            a structured 3-page PDF roadmap covering skills, projects, roles, and targeted companies.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("Capabilities")
        st.markdown("""
        <div class="card">
            <ul>
                <li>Supports 9 domains — Finance, Healthcare, Supply Chain, E-Commerce, HR Analytics, Automobile, Manufacturing, Retail, and Cyber Security.</li>
                <li>AI generates personalised prescription text with domain-specific bullets using Groq LLaMA 3.3 70B.</li>
                <li>Produces a professional 3-page PDF with header, career table, services table, and reveal box.</li>
                <li>Career table includes roles, challenges, key skills, and targeted companies per domain.</li>
                <li>Page 3 merges from a template PDF with consistent border across all 3 pages.</li>
                <li>Download ready — PDF generated instantly with student name and timestamp.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.subheader("Business Impact")
        st.markdown("""
        <div class="card">
            <ul>
                <li>Replace manual prescription writing — generate tailored career documents in seconds.</li>
                <li>Deliver consistent, professional-grade prescriptions to every prospective student.</li>
                <li>Showcase domain expertise and placement support in a branded PDF format.</li>
                <li>Scale across hundreds of consultations without additional effort from the team.</li>
                <li>Increase conversion by giving prospects a tangible, personalised career roadmap.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# TAB 2 — APPLICATION
# ════════════════════════════════════════════════════════
with tab2:

    # Asset check
    header_ok = os.path.exists("assets/header.png")
    template_ok = os.path.exists("assets/template.pdf")
    if not (header_ok and template_ok):
        st.error("❌ Missing required assets!")
        st.write(f"{'✅' if header_ok else '❌'} header.png")
        st.write(f"{'✅' if template_ok else '❌'} template.pdf")
        st.stop()

    st.subheader("Your Details")

    with st.form("form"):
        col1, col2 = st.columns(2, gap="large")
        with col1:
            name = st.text_input("Name *", placeholder="e.g. Student Name")
        with col2:
            status = st.selectbox("Status *", ["Working Professional", "Student", "Job Seeker"])

        domains = st.multiselect(
            "Target Domains *",
            ["Finance", "Supply Chain", "Healthcare", "HR Analytics", "E-Commerce",
             "Automobile", "Manufacturing", "Retail", "Cyber Security"],
            help="Select 1–3 domains"
        )
        submit = st.form_submit_button("🚀 Generate Prescription")

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
            with st.spinner("🤖 AI generating prescription..."):
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
                            "⬇️ Download PDF",
                            f,
                            file_name=filename,
                            mime="application/pdf"
                        )
                    with st.expander("📋 AI Content"):
                        st.json(ai_content)
                    with st.expander("📊 Career Data"):
                        st.write(f"**Roles generated:** {len(table_rows)}")
                        st.write(f"**Domains:** {domain_rowspan_map}")
                else:
                    st.error(f"PDF Error: {error_msg}")
