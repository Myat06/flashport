"""
Generates FlashPort technical explainer PDF.
Run: cd backend && source venv/bin/activate && python scripts/generate_explainer.py
Output: data/FlashPort_How_It_Works.pdf
"""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)

OUT = Path(__file__).parent.parent.parent / "docs" / "FlashPort_How_It_Works.pdf"

#  Colours 
BLUE      = colors.HexColor("#1B4FBF")
LBLUE     = colors.HexColor("#E8EEF9")
DBLUE     = colors.HexColor("#0F2E7A")
GREEN     = colors.HexColor("#16A34A")
LGREEN    = colors.HexColor("#DCFCE7")
YELLOW    = colors.HexColor("#CA8A04")
LYELLOW   = colors.HexColor("#FEF9C3")
RED       = colors.HexColor("#DC2626")
LRED      = colors.HexColor("#FEE2E2")
GRAY      = colors.HexColor("#F8F9FA")
DGRAY     = colors.HexColor("#374151")
MGRAY     = colors.HexColor("#6B7280")
CODE_BG   = colors.HexColor("#1E1E2E")
CODE_FG   = colors.HexColor("#CDD6F4")
BORDER    = colors.HexColor("#D1D5DB")

#  Styles 
def make_styles():
    s = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle("ct", fontSize=32, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_CENTER, spaceAfter=6, leading=38),
        "cover_sub":   ParagraphStyle("cs", fontSize=14, fontName="Helvetica",
            textColor=colors.HexColor("#CBD5E1"), alignment=TA_CENTER, spaceAfter=4),
        "cover_tag":   ParagraphStyle("ctag", fontSize=10, fontName="Helvetica",
            textColor=colors.HexColor("#94A3B8"), alignment=TA_CENTER),
        "h1":  ParagraphStyle("h1", fontSize=18, fontName="Helvetica-Bold",
            textColor=DBLUE, spaceAfter=4, spaceBefore=14),
        "h2":  ParagraphStyle("h2", fontSize=13, fontName="Helvetica-Bold",
            textColor=BLUE, spaceAfter=3, spaceBefore=10),
        "h3":  ParagraphStyle("h3", fontSize=10, fontName="Helvetica-Bold",
            textColor=DGRAY, spaceAfter=2, spaceBefore=6),
        "body": ParagraphStyle("body", fontSize=9, fontName="Helvetica",
            textColor=DGRAY, leading=14, spaceAfter=4, alignment=TA_JUSTIFY),
        "body_c": ParagraphStyle("bodyc", fontSize=9, fontName="Helvetica",
            textColor=DGRAY, leading=14, spaceAfter=4, alignment=TA_CENTER),
        "code": ParagraphStyle("code", fontSize=8, fontName="Courier",
            textColor=CODE_FG, leading=12, spaceAfter=2,
            leftIndent=8, rightIndent=8),
        "code_comment": ParagraphStyle("codecmt", fontSize=8, fontName="Courier",
            textColor=colors.HexColor("#6C7086"), leading=12),
        "label": ParagraphStyle("label", fontSize=8, fontName="Helvetica-Bold",
            textColor=BLUE, spaceAfter=1),
        "small": ParagraphStyle("small", fontSize=7.5, fontName="Helvetica",
            textColor=MGRAY, leading=11),
        "footer": ParagraphStyle("footer", fontSize=7, fontName="Helvetica",
            textColor=MGRAY, alignment=TA_CENTER),
        "step_num": ParagraphStyle("sn", fontSize=20, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_CENTER),
        "step_title": ParagraphStyle("st", fontSize=11, fontName="Helvetica-Bold",
            textColor=DBLUE, spaceAfter=2),
        "step_body": ParagraphStyle("sb", fontSize=8.5, fontName="Helvetica",
            textColor=DGRAY, leading=13),
        "tag": ParagraphStyle("tag", fontSize=7.5, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_CENTER),
    }

S = make_styles()

def hr(color=BLUE, thickness=1.5):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6, spaceBefore=2)

def sp(h=4):
    return Spacer(1, h)

def code_block(lines, bg=CODE_BG):
    rows = [[Paragraph(ln, S["code"])] for ln in lines]
    return Table(rows, colWidths=["100%"], style=TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("LEFTPADDING",  (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING",   (0,0), (0,0),    8),
        ("BOTTOMPADDING",(0,-1),(-1,-1),  8),
        ("TOPPADDING",   (0,1), (-1,-1),  1),
        ("BOTTOMPADDING",(0,0), (-1,-2),  1),
        ("ROUNDEDCORNERS", [4]),
    ]))

def info_box(text, bg=LBLUE, border=BLUE):
    return Table([[Paragraph(text, S["body"])]], colWidths=["100%"], style=TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), bg),
        ("BOX",          (0,0), (-1,-1), 1, border),
        ("LEFTPADDING",  (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING",   (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0), (-1,-1), 8),
    ]))

def badge(text, bg, fg=colors.white):
    return Table([[Paragraph(f"<b>{text}</b>", ParagraphStyle("b",
        fontSize=8, fontName="Helvetica-Bold", textColor=fg, alignment=TA_CENTER))]],
        colWidths=[30*mm], style=TableStyle([
            ("BACKGROUND",(0,0),(-1,-1), bg),
            ("TOPPADDING",(0,0),(-1,-1), 3),
            ("BOTTOMPADDING",(0,0),(-1,-1), 3),
            ("ROUNDEDCORNERS",[3]),
        ]))

def step_box(num, title, body_text, color=BLUE):
    num_cell  = Table([[Paragraph(str(num), S["step_num"])]],
        colWidths=[14*mm], rowHeights=[14*mm],
        style=TableStyle([("BACKGROUND",(0,0),(-1,-1), color),
                          ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                          ("ROUNDEDCORNERS",[4])]))
    text_cell = [Paragraph(title, S["step_title"]),
                 Paragraph(body_text, S["step_body"])]
    t = Table([[num_cell, text_cell]], colWidths=[18*mm, "82%"],
        style=TableStyle([
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LEFTPADDING",(0,0),(0,-1), 0),
            ("LEFTPADDING",(1,0),(1,-1), 8),
            ("TOPPADDING",(0,0),(-1,-1), 0),
            ("BOTTOMPADDING",(0,0),(-1,-1), 0),
            ("BACKGROUND",(0,0),(-1,-1), GRAY),
            ("BOX",(0,0),(-1,-1), 0.5, BORDER),
            ("ROUNDEDCORNERS",[4]),
        ]))
    return t

#  Build 
def build():
    doc = SimpleDocTemplate(str(OUT), pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=16*mm, bottomMargin=16*mm)
    story = []

    #  COVER PAGE 
    cover_bg = Table(
        [[Paragraph("FlashPort", S["cover_title"])],
         [Paragraph("How It Works", S["cover_sub"])],
         [sp(6)],
         [Paragraph("AI-Powered Customs Declaration Automation", S["cover_sub"])],
         [Paragraph("OCR Pipeline  |  Risk Scoring  |  XGBoost Training", S["cover_tag"])],
         [sp(10)],
         [Paragraph("AI Open Innovation Challenge 2026  -  Case 1: Cikarang Dry Port", S["cover_tag"])],
         [Paragraph("Team: Teknik Logistik  -  President University", S["cover_tag"])],
        ],
        colWidths=["100%"],
        style=TableStyle([
            ("BACKGROUND",(0,0),(-1,-1), DBLUE),
            ("TOPPADDING",(0,0),(-1,-1), 6),
            ("BOTTOMPADDING",(0,0),(-1,-1), 6),
            ("LEFTPADDING",(0,0),(-1,-1), 20),
            ("RIGHTPADDING",(0,0),(-1,-1), 20),
            ("TOPPADDING",(0,0),(0,0), 30),
            ("BOTTOMPADDING",(0,-1),(-1,-1), 30),
        ])
    )
    story += [cover_bg, sp(16)]

    # Quick summary boxes
    summary = [
        [Paragraph("<b>[ MOBILE ]</b><br/>Mobile App<br/>Offline-first camera scan", S["body_c"]),
         Paragraph("<b>[ BACKEND ]</b><br/>FastAPI Backend<br/>OCR + AI extraction", S["body_c"]),
         Paragraph("<b>[ WEB ]</b><br/>Web Dashboard<br/>Manager review + CEISA", S["body_c"])],
    ]
    story.append(Table(summary, colWidths=["33%","34%","33%"], style=TableStyle([
        ("BOX",(0,0),(-1,-1), 1, BLUE),
        ("INNERGRID",(0,0),(-1,-1), 0.5, LBLUE),
        ("BACKGROUND",(0,0),(-1,-1), GRAY),
        ("TOPPADDING",(0,0),(-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("ROUNDEDCORNERS",[4]),
    ])))
    story += [sp(8),
        Paragraph("This document explains the complete technical flow  from the moment a field operator "
            "takes a photo of a trade document, to the AI extracting customs fields, scoring risk, "
            "and sending the result to the manager's dashboard. It also explains how the XGBoost "
            "risk model was trained.", S["body"]),
        PageBreak()]

    #  PART 1: BACKEND FLOW 
    story += [
        Paragraph("PART 1  The OCR Pipeline", S["h1"]), hr(),
        Paragraph(
            "Every time an operator uploads a document (photo or PDF), the backend runs "
            "this exact sequence of steps. Nothing is manual  the entire process from raw "
            "image to risk score happens automatically in under 3 seconds.",
            S["body"]),
        sp(6),
    ]

    # Flow diagram
    flow_rows = [
        [Paragraph("MOBILE", S["tag"]),
         Paragraph("", S["tag"]),
         Paragraph("BACKEND", S["tag"]),
         Paragraph("", S["tag"]),
         Paragraph("DATABASE", S["tag"])],
        [Paragraph("Take photo\nor attach file", S["small"]),
         Paragraph("\nPOST /sync\n(base64 image)", S["small"]),
         Paragraph("OpenCV\npreprocess\n+ Tesseract OCR", S["small"]),
         Paragraph("\nextract fields\n+ score risk", S["small"]),
         Paragraph("save result\n+ push to\ndashboard", S["small"])],
    ]
    story.append(Table(flow_rows, colWidths=["18%","14%","22%","14%","18%"],
        style=TableStyle([
            ("BACKGROUND",(0,0),(0,0), BLUE),
            ("BACKGROUND",(2,0),(2,0), DBLUE),
            ("BACKGROUND",(4,0),(4,0), GREEN),
            ("BACKGROUND",(1,0),(1,0), GRAY),
            ("BACKGROUND",(3,0),(3,0), GRAY),
            ("BACKGROUND",(0,1),(-1,-1), GRAY),
            ("TEXTCOLOR",(0,0),(0,0), colors.white),
            ("TEXTCOLOR",(2,0),(2,0), colors.white),
            ("TEXTCOLOR",(4,0),(4,0), colors.white),
            ("BOX",(0,0),(-1,-1), 0.5, BORDER),
            ("INNERGRID",(0,0),(-1,-1), 0.3, BORDER),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("TOPPADDING",(0,0),(-1,-1), 6),
            ("BOTTOMPADDING",(0,0),(-1,-1), 6),
            ("FONTNAME",(0,1),(-1,-1),"Helvetica"),
            ("FONTSIZE",(0,1),(-1,-1), 8),
        ])))
    story += [sp(10)]

    # Step 1
    story += [
        step_box(1, "Mobile sends the image",
            "The operator's photo is compressed from ~3MB to ~300KB using flutter_image_compress, "
            "then converted to base64 text and sent to the backend as a JSON payload."),
        sp(4),
    ]
    story.append(code_block([
        '<font color="#89B4FA">POST</font> /sync',
        '{',
        '  <font color="#A6E3A1">"scan_id"</font>:        <font color="#F9E2AF">"abc-123-uuid"</font>,',
        '  <font color="#A6E3A1">"document_type"</font>: <font color="#F9E2AF">"commercial_invoice"</font>,',
        '  <font color="#A6E3A1">"operator_id"</font>:   <font color="#F9E2AF">"CDP-001"</font>,',
        '  <font color="#A6E3A1">"image_b64"</font>:     <font color="#F9E2AF">"/9j/4AAQSkZJRgAB..."</font>  <font color="#6C7086"> your photo, base64 encoded</font>',
        '}',
    ]))
    story += [sp(8)]

    # Step 2
    story += [
        step_box(2, "Detect file type  PDF or image?",
            "Base64 encoded files always start with a predictable header. The backend checks this "
            "to decide how to process it. PDFs need to be converted to images first."),
        sp(4),
    ]
    story.append(code_block([
        '<font color="#6C7086"># PDF base64 always starts with "JVBERi0" (that is %PDF- in base64)</font>',
        '<font color="#6C7086"># JPEG starts with "/9j/"    PNG starts with "iVBORw"</font>',
        '',
        '<font color="#89B4FA">if</font> is_pdf(payload.image_b64):',
        '    images = decode_pdf_pages(payload.image_b64)   <font color="#6C7086"># one image per page</font>',
        '    text = <font color="#F9E2AF">"\n"</font>.join(run_tesseract(preprocess(img)) <font color="#89B4FA">for</font> img <font color="#89B4FA">in</font> images)',
        '<font color="#89B4FA">else</font>:',
        '    text = run_tesseract(preprocess(decode_image(payload.image_b64)))',
    ]))
    story += [sp(8)]

    # Step 3
    story += [
        step_box(3, "OpenCV preprocessing  clean up the image",
            "Raw photos are often blurry, skewed, or have bad lighting. OpenCV fixes this before "
            "Tesseract reads it, which dramatically improves accuracy."),
        sp(4),
    ]
    before_after = [
        [Paragraph("<b>Before preprocessing</b>", S["label"]),
         Paragraph("<b>After preprocessing</b>", S["label"])],
        [Paragraph("Color photo, shadows, slight angle, noise", S["small"]),
         Paragraph("Black & white, straight, clean  ready for OCR", S["small"])],
        [Paragraph(
            "HS Code: 8471.30.00   might be read as\n"
            "H5 C0de: 847l.3O.OO  (0 vs O, l vs 1)", S["small"]),
         Paragraph(
            "HS Code: 8471.30.00   clean text\n"
            "Tesseract reads this correctly every time", S["small"])],
    ]
    story.append(Table(before_after, colWidths=["50%","50%"], style=TableStyle([
        ("BOX",(0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",(0,0),(-1,-1), 0.3, BORDER),
        ("BACKGROUND",(0,0),(-1,0), LBLUE),
        ("BACKGROUND",(0,1),(0,-1), LRED),
        ("BACKGROUND",(1,1),(1,-1), LGREEN),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1), 8),
    ])))
    story.append(code_block([
        'gray   = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)      <font color="#6C7086"># remove color</font>',
        'thresh = cv2.adaptiveThreshold(gray, 255,              <font color="#6C7086"># make text pure black</font>',
        '             cv2.ADAPTIVE_THRESH_GAUSSIAN_C,           <font color="#6C7086">#   background pure white</font>',
        '             cv2.THRESH_BINARY, 11, 2)',
        '<font color="#6C7086"># deskew: rotate image back to straight if taken at an angle</font>',
    ]))
    story += [sp(8)]

    # Step 4
    story += [
        step_box(4, "Tesseract OCR  image to raw text",
            "Tesseract reads the cleaned image and outputs everything it sees as plain text. "
            "This is not structured yet  just a big string of characters, including all labels, "
            "values, headers, and even noise."),
        sp(4),
    ]
    story.append(code_block([
        'text = pytesseract.image_to_string(',
        '    image,',
        '    lang=<font color="#F9E2AF">"eng+ind"</font>,   <font color="#6C7086"># English + Indonesian language packs</font>',
        '    config=<font color="#F9E2AF">"--psm 6"</font>  <font color="#6C7086"># treat as a uniform block of text</font>',
        ')',
    ]))
    story += [sp(4)]
    story.append(Table([[
        Paragraph("<b>Example Tesseract output (raw):</b>", S["label"]),
    ]], colWidths=["100%"]))
    story.append(code_block([
        'COMMERCIAL INVOICE  /  Faktur Komersial',
        'Invoice No.: INV-2026-5969          Date: 13 April 2026',
        'SHIPPER / EXPORTER                  CONSIGNEE / IMPORTER',
        'Apple Inc.                          PT LG Electronics Indonesia',
        'One Apple Park Way, Cupertino       Jl. Jend. Gatot Subroto Kav. 9-11',
        'PORT OF LOADING    PORT OF DISCHARGE    CONTAINER NO.',
        'Rotterdam          Cikarang Dry Port    YMLU7593824',
        'HS Code    Description              Qty    Unit Price    Amount',
        '8471.30.00 Portable Auto Data...   91     1,470.34      USD 133,800.94',
        'Net Weight: 460.59 KG              Gross Weight: 497.44 KG',
    ]))
    story += [sp(4),
        info_box("NOTE: This is just raw text  no structure, no fields. The regex extractor "
            "in Step 5 turns this into individual named values.", LBLUE, BLUE),
        sp(8)]

    # Step 5
    story += [
        step_box(5, "Regex field extractor  find specific values",
            "Regular expressions (regex) are patterns that scan the raw text and extract "
            "specific values. Each field has its own pattern tuned for customs document formats."),
        sp(4),
    ]
    regex_rows = [
        [Paragraph("<b>Field</b>", S["label"]),
         Paragraph("<b>Pattern</b>", S["label"]),
         Paragraph("<b>Finds in the text</b>", S["label"]),
         Paragraph("<b>Result</b>", S["label"])],
        ["HS Code",
         Paragraph(r"<font face='Courier'>\d{4}[.]\d{2}[.]\d{2}</font>", S["small"]),
         "4-2-2 digit structure",
         Paragraph("<b>8471.30.00</b>", S["small"])],
        ["Invoice Value",
         Paragraph(r"<font face='Courier'>USD\s*[\d,]+\.\d{2}</font>", S["small"]),
         "Currency code + numbers",
         Paragraph("<b>USD 133,800.94</b>", S["small"])],
        ["Container ID",
         Paragraph(r"<font face='Courier'>[A-Z]{4}\d{7}</font>", S["small"]),
         "4 letters + 7 digits",
         Paragraph("<b>YMLU7593824</b>", S["small"])],
        ["Importer",
         Paragraph(r"<font face='Courier'>CONSIGNEE[\s:]+([A-Z].*)</font>", S["small"]),
         "Label then company name",
         Paragraph("<b>PT LG Electronics Indonesia</b>", S["small"])],
        ["Net Weight",
         Paragraph(r"<font face='Courier'>[\d.]+\s*KG</font>", S["small"]),
         "Number + KG",
         Paragraph("<b>460.59 KG</b>", S["small"])],
        ["Vessel",
         Paragraph(r"<font face='Courier'>(?:MV|MT|SS)\s+\S+</font>", S["small"]),
         "MV/MT/SS prefix",
         Paragraph("<b>MV Yang Ming Wellness</b>", S["small"])],
    ]
    story.append(Table(regex_rows, colWidths=["16%","28%","28%","28%"], style=TableStyle([
        ("BOX",(0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",(0,0),(-1,-1), 0.3, BORDER),
        ("BACKGROUND",(0,0),(-1,0), BLUE),
        ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("BACKGROUND",(0,1),(-1,-1), GRAY),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, GRAY]),
        ("LEFTPADDING",(0,0),(-1,-1), 6),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("FONTSIZE",(0,0),(-1,-1), 8),
    ])))
    story += [sp(4),
        Paragraph("After all patterns run, the result is a clean Python object with named fields:", S["body"]),
        sp(2)]
    story.append(code_block([
        'ExtractionResult(',
        '    hs_code        = <font color="#F9E2AF">"8471.30.00"</font>,',
        '    invoice_value  = <font color="#F9E2AF">"USD 133,800.94"</font>,',
        '    container_id   = <font color="#F9E2AF">"YMLU7593824"</font>,',
        '    importer       = <font color="#F9E2AF">"PT LG Electronics Indonesia"</font>,',
        '    exporter       = <font color="#F9E2AF">"Apple Inc."</font>,',
        '    net_weight     = <font color="#F9E2AF">"460.59 KG"</font>,',
        '    vessel_name    = <font color="#F9E2AF">"MV Yang Ming Wellness"</font>,',
        '    port_of_origin = <font color="#F9E2AF">"Rotterdam, Netherlands"</font>,',
        '    missing_critical = <font color="#A6E3A1">[]</font>   <font color="#6C7086"># nothing missing  great!</font>',
        ')',
    ]))
    story += [sp(8), PageBreak()]

    # Step 6
    story += [
        step_box(6, "XGBoost risk scoring  predict the lane",
            "The extracted fields are converted to 16 numbers (features) and fed into the "
            "XGBoost model. The model outputs probabilities for each lane and we compute a "
            "0100 risk score."),
        sp(4),
    ]
    feat_rows = [
        [Paragraph("<b>Feature</b>", S["label"]),
         Paragraph("<b>Value (this doc)</b>", S["label"]),
         Paragraph("<b>Why it matters</b>", S["label"])],
        ["has_hs_code",        "1  (present)",   "Missing HS code = immediate risk"],
        ["has_invoice_value",  "1  (present)",   "Customs needs declared value"],
        ["has_container_id",   "1  (present)",   "Can't track goods without it"],
        ["has_importer",       "1  (present)",   "Who receives the goods"],
        ["has_exporter",       "1  (present)",   "Who sent the goods"],
        ["has_vessel",         "1  (present)",   "Which ship carried it"],
        ["has_port",           "1  (present)",   "Country of origin"],
        ["missing_field_count","0  (none)",       "Total critical fields missing"],
        ["confidence_score",   "2  (high)",       "OCR quality: high=2 medium=1 low=0"],
        ["is_restricted_hs",   "0  (no)",        "Weapons / chemicals = restricted"],
        ["invoice_value_log",  "11.8",           "log(133,800)  log scale handles large values"],
        ["is_high_value",      "1  (>USD 50k)",  "High value shipments get extra scrutiny"],
        ["high_val_no_cont",   "0  (has cont.)", "High value without container = very suspicious"],
        ["hs_high_scrutiny",   "1  (yes)",       "Electronics = moderate scrutiny category"],
    ]
    story.append(Table(feat_rows, colWidths=["32%","24%","44%"], style=TableStyle([
        ("BOX",(0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",(0,0),(-1,-1), 0.3, BORDER),
        ("BACKGROUND",(0,0),(-1,0), DBLUE),
        ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, GRAY]),
        ("LEFTPADDING",(0,0),(-1,-1), 6),
        ("TOPPADDING",(0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1), 8),
    ])))
    story += [sp(4)]
    story.append(code_block([
        '<font color="#6C7086"># Model outputs probability for each lane:</font>',
        'proba = model.predict_proba([features])[0]',
        '<font color="#6C7086">#  [0.71,  0.22,  0.07]</font>',
        '<font color="#6C7086">#                 </font>',
        '<font color="#6C7086">#   Green  Yellow  Red</font>',
        '',
        '<font color="#6C7086"># Convert to 0-100 risk score:</font>',
        'risk_score = P(yellow) × 40  +  P(red) × 100',
        '           = 0.22 × 40  +  0.07 × 100',
        '           = 8.8  +  7.0  =  <font color="#A6E3A1">15.8    16%    GREEN LANE </font>',
    ]))
    story += [sp(6)]

    # Lane result boxes
    lane_data = [
        [Paragraph("GREEN LANE", ParagraphStyle("g", fontSize=10, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_CENTER)),
         Paragraph("YELLOW LANE", ParagraphStyle("y", fontSize=10, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_CENTER)),
         Paragraph("RED LANE", ParagraphStyle("r", fontSize=10, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_CENTER))],
        [Paragraph("Risk score < 30%\nAll fields present\nClean declaration\n Immediate release", S["small"]),
         Paragraph("Risk score 3070%\nSome fields missing\nor medium confidence\n Document verification", S["small"]),
         Paragraph("Risk score > 70%\nRestricted HS code\nWatchlist hit / missing\ncritical fields\n Physical inspection", S["small"])],
    ]
    story.append(Table(lane_data, colWidths=["33%","34%","33%"], style=TableStyle([
        ("BACKGROUND",(0,0),(0,0), GREEN),
        ("BACKGROUND",(1,0),(1,0), YELLOW),
        ("BACKGROUND",(2,0),(2,0), RED),
        ("BACKGROUND",(0,1),(0,1), LGREEN),
        ("BACKGROUND",(1,1),(1,1), LYELLOW),
        ("BACKGROUND",(2,1),(2,1), LRED),
        ("BOX",(0,0),(-1,-1), 1, BORDER),
        ("INNERGRID",(0,0),(-1,-1), 0.5, BORDER),
        ("ALIGN",(0,0),(-1,0),"CENTER"),
        ("ALIGN",(0,1),(-1,-1),"CENTER"),
        ("LEFTPADDING",(0,0),(-1,-1), 6),
        ("TOPPADDING",(0,0),(-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("FONTSIZE",(0,1),(-1,-1), 8),
    ])))
    story += [sp(8)]

    # Step 7
    story += [
        step_box(7, "Save to database + push to dashboard",
            "Everything is saved to PostgreSQL  including the original document image in base64 "
            "so the manager can view it. The result is broadcast live to the web dashboard "
            "via WebSocket, and a push notification is sent to the operator's phone."),
        sp(6),
    ]
    story.append(code_block([
        '<font color="#6C7086"># Save to PostgreSQL</font>',
        'declaration = Declaration(',
        '    scan_id       = <font color="#F9E2AF">"abc-123"</font>,',
        '    hs_code       = <font color="#F9E2AF">"8471.30.00"</font>,',
        '    risk_score    = <font color="#A6E3A1">16</font>,',
        '    risk_badge    = <font color="#A6E3A1">"green"</font>,',
        '    image_data    = <font color="#F9E2AF">"<base64 of original photo>"</font>,',
        '    ceisa_ready   = <font color="#A6E3A1">True</font>,',
        ')',
        '',
        '<font color="#6C7086"># Push live to web dashboard</font>',
        '<font color="#89B4FA">await</font> broadcast({ <font color="#F9E2AF">"event"</font>: <font color="#F9E2AF">"new_declaration"</font>, <font color="#F9E2AF">"data"</font>: response })',
        '',
        '<font color="#6C7086"># Return result to mobile app</font>',
        '<font color="#89B4FA">return</font> { <font color="#F9E2AF">"risk_score"</font>: <font color="#A6E3A1">16</font>, <font color="#F9E2AF">"risk_badge"</font>: <font color="#A6E3A1">"green"</font>, <font color="#F9E2AF">"ceisa_ready"</font>: <font color="#A6E3A1">True</font> }',
    ]))
    story += [sp(8), PageBreak()]

    #  PART 2: TRAINING 
    story += [
        Paragraph("PART 2  How XGBoost Was Trained", S["h1"]), hr(),
        Paragraph(
            "The XGBoost risk model was trained on 600 synthetic customs declarations "
            "designed to reflect real patterns at Cikarang Dry Port. Here is exactly how "
            "the training data was built and how the model learned from it.",
            S["body"]),
        sp(8),
    ]

    # Training step 1
    story += [
        step_box(1, "Generate 600 realistic fake declarations",
            "A Python script generated records that look like real Cikarang Dry Port data  "
            "with realistic company names, HS codes, container IDs, vessels, and ports.", DBLUE),
        sp(4),
    ]
    dist_rows = [
        [Paragraph("<b>Profile</b>", S["label"]),
         Paragraph("<b>Count</b>", S["label"]),
         Paragraph("<b>What it looks like</b>", S["label"]),
         Paragraph("<b>Label</b>", S["label"])],
        ["Clean (55%)", "330",
         "All fields present, valid HS code, high confidence",
         Paragraph("<b>Green</b>", ParagraphStyle("g",fontSize=8,fontName="Helvetica-Bold",textColor=GREEN))],
        ["Partial (25%)", "150",
         "12 non-critical fields missing (vessel, port, carton count)",
         Paragraph("<b>Yellow</b>", ParagraphStyle("y",fontSize=8,fontName="Helvetica-Bold",textColor=YELLOW))],
        ["Missing (12%)", "72",
         "24 critical fields missing (HS code, importer, value, container)",
         Paragraph("<b>Red</b>", ParagraphStyle("r",fontSize=8,fontName="Helvetica-Bold",textColor=RED))],
        ["Risky (8%)", "48",
         "Restricted HS code (weapons/chemicals), very high value, low OCR confidence",
         Paragraph("<b>Red</b>", ParagraphStyle("r",fontSize=8,fontName="Helvetica-Bold",textColor=RED))],
    ]
    story.append(Table(dist_rows, colWidths=["18%","12%","50%","20%"], style=TableStyle([
        ("BOX",(0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",(0,0),(-1,-1), 0.3, BORDER),
        ("BACKGROUND",(0,0),(-1,0), DBLUE),
        ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, GRAY]),
        ("LEFTPADDING",(0,0),(-1,-1), 6),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("FONTSIZE",(0,0),(-1,-1), 8),
    ])))
    story += [sp(4)]
    story.append(code_block([
        '<font color="#6C7086"># Example clean record (Green):</font>',
        '{ "hs_code": <font color="#F9E2AF">"8471.30.00"</font>, "invoice_value": <font color="#F9E2AF">"USD 37,414.23"</font>,',
        '  "container_id": <font color="#F9E2AF">"APHU6497677"</font>, "importer": <font color="#F9E2AF">"PT Garudafood Putra Putri Jaya"</font>,',
        '  "exporter": <font color="#F9E2AF">"Posco Co., Ltd"</font>, "confidence": <font color="#F9E2AF">"high"</font>,',
        '  "jalur": <font color="#A6E3A1">"green"</font>, "jalur_label": <font color="#A6E3A1">0</font> }',
        '',
        '<font color="#6C7086"># Example risky record (Red):</font>',
        '{ "hs_code": <font color="#F9E2AF">"9301.00.00"</font>,  <font color="#6C7086"> military weapons</font>',
        '  "invoice_value": <font color="#F9E2AF">"USD 2,069,981"</font>, "exporter": <font color="#F9E2AF">""</font>,  <font color="#6C7086"> missing</font>',
        '  "confidence": <font color="#F9E2AF">"medium"</font>,',
        '  "jalur": <font color="#F38BA8">"red"</font>, "jalur_label": <font color="#F38BA8">2</font> }',
    ]))
    story += [sp(8)]

    # Training step 2
    story += [
        step_box(2, "Convert records to feature vectors",
            "Every record becomes 16 numbers  this is called a feature vector. "
            "XGBoost only understands numbers, not text.", DBLUE),
        sp(4),
    ]
    story.append(code_block([
        '<font color="#6C7086"># Clean record  feature vector:</font>',
        'features = [',
        '  has_hs_code=<font color="#A6E3A1">1</font>, has_invoice=<font color="#A6E3A1">1</font>, has_container=<font color="#A6E3A1">1</font>, has_importer=<font color="#A6E3A1">1</font>,',
        '  has_exporter=<font color="#A6E3A1">1</font>, has_vessel=<font color="#A6E3A1">1</font>, has_port=<font color="#A6E3A1">1</font>,',
        '  missing_count=<font color="#A6E3A1">0</font>, confidence=<font color="#A6E3A1">2</font>, is_restricted=<font color="#A6E3A1">0</font>,',
        '  invoice_log=<font color="#A6E3A1">10.5</font>, is_high_value=<font color="#A6E3A1">0</font>, ...   label: <font color="#A6E3A1">0 (green)</font>',
        ']',
        '',
        '<font color="#6C7086"># Risky record  feature vector:</font>',
        'features = [',
        '  has_hs_code=<font color="#A6E3A1">1</font>, has_invoice=<font color="#A6E3A1">1</font>, has_container=<font color="#A6E3A1">1</font>, has_importer=<font color="#A6E3A1">1</font>,',
        '  has_exporter=<font color="#F38BA8">0</font>, has_vessel=<font color="#A6E3A1">1</font>, has_port=<font color="#A6E3A1">1</font>,',
        '  missing_count=<font color="#F38BA8">1</font>, confidence=<font color="#F9E2AF">1</font>, is_restricted=<font color="#F38BA8">1</font>,',
        '  invoice_log=<font color="#F38BA8">14.5</font>, is_high_value=<font color="#F38BA8">1</font>, ...   label: <font color="#F38BA8">2 (red)</font>',
        ']',
        '',
        '<font color="#6C7086"># 600 rows × 16 columns = the training matrix</font>',
    ]))
    story += [sp(8)]

    # Training step 3
    story += [
        step_box(3, "XGBoost builds decision trees",
            "XGBoost (eXtreme Gradient Boosting) builds 300 decision trees one after another. "
            "Each tree learns to fix the mistakes of the previous one. This process is called "
            'boosting  each tree "boosts" the accuracy of the model.', DBLUE),
        sp(4),
    ]
    tree_ex = [
        [Paragraph("<b>Simplified example of what one tree learned:</b>", S["label"])],
        [code_block([
            'Tree #1:',
            '  Is hs_code restricted? (weapons/chemicals)',
            '   YES  predict RED  (high risk)',
            '   NO  ',
            '        Are more than 2 critical fields missing?',
            '         YES  predict YELLOW or RED',
            '         NO  ',
            '              Is OCR confidence low?',
            '               YES  predict YELLOW',
            '               NO   predict GREEN',
            '',
            'Tree #2  corrects mistakes Tree #1 made',
            'Tree #3  corrects mistakes Tree #2 made',
            '... (300 trees total)',
        ])],
    ]
    story.append(Table(tree_ex, colWidths=["100%"], style=TableStyle([
        ("LEFTPADDING",(0,0),(-1,-1), 0),
        ("RIGHTPADDING",(0,0),(-1,-1), 0),
        ("TOPPADDING",(0,0),(-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
    ])))
    story += [sp(8)]

    # Training step 4
    story += [
        step_box(4, "Results  89.5% accuracy on cross-validation",
            "We tested the model using 5-fold cross-validation: split the 600 records into "
            "5 groups, train on 4, test on 1, repeat 5 times. Average accuracy was 89.5%.", DBLUE),
        sp(4),
    ]
    results_rows = [
        [Paragraph("<b>Metric</b>", S["label"]),
         Paragraph("<b>Value</b>", S["label"]),
         Paragraph("<b>Meaning</b>", S["label"])],
        ["CV Accuracy",     "89.5%",  "Correct prediction 9 out of 10 times on unseen data"],
        ["Green precision", "100%",   "When model says Green  always Green"],
        ["Yellow recall",   "100%",   "Catches every Yellow declaration"],
        ["Red recall",      "97%",    "Misses 2 Red out of 78 (predicted Yellow instead)"],
        ["Training time",   "< 3 sec","Fast to retrain when you get real data"],
    ]
    story.append(Table(results_rows, colWidths=["25%","15%","60%"], style=TableStyle([
        ("BOX",(0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",(0,0),(-1,-1), 0.3, BORDER),
        ("BACKGROUND",(0,0),(-1,0), DBLUE),
        ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, GRAY]),
        ("LEFTPADDING",(0,0),(-1,-1), 6),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("FONTSIZE",(0,0),(-1,-1), 8),
    ])))
    story += [sp(4)]

    # Feature importance
    story += [Paragraph("<b>Top feature importances</b>  what the model cares about most:", S["label"]), sp(2)]
    importance = [
        ("is_restricted_hs",      36.5, "Restricted HS code (weapons, chemicals) is by far the strongest signal"),
        ("hs_high_scrutiny",       10.7, "Electronics, petroleum categories  moderate scrutiny"),
        ("missing_field_count",     8.0, "How many critical fields are empty"),
        ("has_port",                6.0, "Port of origin present or not"),
        ("has_container_id",        4.6, "Container ID present or not"),
        ("high_val_no_container",   4.6, "High value shipment without container ID"),
        ("has_hs_code",             4.5, "HS code present or not"),
        ("has_vessel",              4.0, "Vessel name present or not"),
    ]
    imp_rows = [[Paragraph("<b>Feature</b>", S["label"]),
                 Paragraph("<b>Importance</b>", S["label"]),
                 Paragraph("<b>Bar</b>", S["label"]),
                 Paragraph("<b>Why</b>", S["label"])]]
    for feat, pct, why in importance:
        bar_w = int(pct / 40 * 100)
        bar_table = Table([[""]], colWidths=[f"{bar_w}%"],
            style=TableStyle([("BACKGROUND",(0,0),(-1,-1), BLUE),
                              ("TOPPADDING",(0,0),(-1,-1), 4),
                              ("BOTTOMPADDING",(0,0),(-1,-1), 4)]))
        imp_rows.append([
            Paragraph(f"<font face='Courier'>{feat}</font>", S["small"]),
            Paragraph(f"<b>{pct}%</b>", S["small"]),
            bar_table,
            Paragraph(why, S["small"]),
        ])
    story.append(Table(imp_rows, colWidths=["28%","12%","15%","45%"], style=TableStyle([
        ("BOX",(0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",(0,0),(-1,-1), 0.3, BORDER),
        ("BACKGROUND",(0,0),(-1,0), DBLUE),
        ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, GRAY]),
        ("LEFTPADDING",(0,0),(-1,-1), 6),
        ("TOPPADDING",(0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("FONTSIZE",(0,0),(-1,-1), 8),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ])))
    story += [sp(8)]

    # Training step 5
    story += [
        step_box(5, "Model saved  loaded once at startup",
            "The trained model is saved to a file and loaded into memory when the backend starts. "
            "Every scan after that uses the model instantly  no re-training needed per scan.", DBLUE),
        sp(4),
    ]
    story.append(code_block([
        '<font color="#6C7086"># Save after training:</font>',
        'model.save_model(<font color="#F9E2AF">"backend/models/risk_model.xgb"</font>)',
        '',
        '<font color="#6C7086"># Load once when backend starts (risk_scorer.py):</font>',
        '_MODEL = xgb.XGBClassifier()',
        '_MODEL.load_model(<font color="#F9E2AF">"backend/models/risk_model.xgb"</font>)',
        '',
        '<font color="#6C7086"># Use on every scan (instant):</font>',
        'proba = _MODEL.predict_proba([features])[0]   <font color="#6C7086"># [p_green, p_yellow, p_red]</font>',
    ]))
    story += [sp(8), PageBreak()]

    #  PART 3: HOW TO RETRAIN
    story += [
        Paragraph("PART 3  How to Retrain the Models", S["h1"]), hr(),
        Paragraph(
            "Both the XGBoost risk model and the spaCy NER model can be retrained at any time "
            "by running four simple scripts. The whole process takes under 2 minutes. "
            "Run them in this order:",
            S["body"]),
        sp(8),
    ]

    story += [
        step_box(1, "Regenerate synthetic training data (600 declarations)",
            "Generates a fresh set of 600 realistic Indonesian customs declarations covering "
            "Commercial Invoice, Bill of Lading, and Packing List. Uses real company names, "
            "HS codes, container IDs, vessels, and ports.", DBLUE),
        sp(4),
    ]
    story.append(code_block([
        'python scripts/generate_training_data.py',
        '',
        '<font color="#6C7086"># Output: data/training_declarations.csv</font>',
        '<font color="#6C7086"># 600 records: 395 Green / 127 Yellow / 78 Red</font>',
        '<font color="#6C7086"># Distribution: Clean 55% | Partial 25% | Missing 12% | Risky 8%</font>',
    ]))
    story += [sp(8)]

    story += [
        step_box(2, "Retrain XGBoost risk model",
            "Reads the CSV, builds 16 feature vectors per record, runs 5-fold cross-validation, "
            "trains the final model on all 600 records, and saves to disk.", DBLUE),
        sp(4),
    ]
    story.append(code_block([
        'python scripts/train_risk_model.py',
        '',
        '<font color="#6C7086"># Output: models/risk_model.xgb</font>',
        '<font color="#6C7086">#         models/model_info.json</font>',
        '<font color="#6C7086"># CV accuracy: 89.5%  |  Training time: < 3 seconds</font>',
    ]))
    story += [sp(8)]

    story += [
        step_box(3, "Generate sample documents — 100 PDFs + 100 PNGs per type",
            "Creates realistic Indonesian customs documents as actual PDF and PNG files. "
            "These are used to test and train the OCR extraction pipeline on real document layouts. "
            "Total: 300 PDFs + 300 PNGs across all three document types.", DBLUE),
        sp(4),
    ]
    story.append(code_block([
        'python scripts/generate_sample_docs.py',
        '',
        '<font color="#6C7086"># Output: data/sample_docs/</font>',
        '<font color="#6C7086">#   commercial_invoice/</font>',
        '<font color="#6C7086">#     docs/    <- 100 PDFs  (real text layer, pypdf extracts directly)</font>',
        '<font color="#6C7086">#     images/  <- 100 PNGs  (300 DPI, Tesseract OCR ready)</font>',
        '<font color="#6C7086">#   bill_of_lading/</font>',
        '<font color="#6C7086">#     docs/    <- 100 PDFs</font>',
        '<font color="#6C7086">#     images/  <- 100 PNGs</font>',
        '<font color="#6C7086">#   packing_list/</font>',
        '<font color="#6C7086">#     docs/    <- 100 PDFs</font>',
        '<font color="#6C7086">#     images/  <- 100 PNGs</font>',
        '<font color="#6C7086"># Uses: real PT company names, HS codes, vessels, ports, container IDs</font>',
    ]))
    story += [sp(8)]

    story += [
        step_box(4, "Regenerate NER training examples (300 annotated texts)",
            "Generates 300 annotated text examples from the same data pools — covering "
            "English and Indonesian label variations for all 11 entity types.", DBLUE),
        sp(4),
    ]
    story.append(code_block([
        'python scripts/generate_ner_training.py',
        '',
        '<font color="#6C7086"># Output: data/ner_training.spacy</font>',
        '<font color="#6C7086"># 300 examples across: commercial invoice, bill of lading, packing list</font>',
        '<font color="#6C7086"># Entity distribution: CONTAINER_ID 296 | HS_CODE 298 | IMPORTER 296 | ...</font>',
    ]))
    story += [sp(8)]

    story += [
        step_box(5, "Retrain spaCy NER model",
            "Fine-tunes en_core_web_sm on the 300 annotated examples. Uses early stopping "
            "so it stops automatically when it reaches peak accuracy.", DBLUE),
        sp(4),
    ]
    story.append(code_block([
        'python scripts/train_ner_model.py',
        '',
        '<font color="#6C7086"># Output: models/ner_model/</font>',
        '<font color="#6C7086"># Typically converges at iteration 15</font>',
        '<font color="#6C7086"># F1: 1.000 on all 11 entity types</font>',
    ]))
    story += [sp(8)]

    story += [
        step_box(6, "Restart the backend — models load automatically",
            "The backend loads both models once at startup. After retraining just restart "
            "the server — no code changes needed.", DBLUE),
        sp(4),
    ]
    story.append(code_block([
        'uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload',
        '',
        '<font color="#6C7086"># Models are loaded once at startup:</font>',
        '<font color="#6C7086">#   XGBoost  -> models/risk_model.xgb</font>',
        '<font color="#6C7086">#   spaCy NER -> models/ner_model/</font>',
        '<font color="#6C7086"># Every scan after that uses both models instantly</font>',
    ]))
    story += [sp(6)]

    story.append(info_box(
        "NOTE: You can retrain as many times as you want. Each run generates fresh synthetic "
        "data with different random values from the same realistic data pools — so the model "
        "sees variety each time. The training pipeline is fully automated end-to-end.",
        LBLUE, BLUE))
    story += [sp(8)]

    # ── PART 4: UPLOAD + DOCUMENT TYPES ──────────────────────────────────────
    story += [PageBreak(),
        Paragraph("PART 4  Mobile Upload Flow + Document Types", S["h1"]), hr(),
        Paragraph(
            "When an operator takes a photo or attaches a file, this is exactly what "
            "happens on the mobile app and how the backend decides which processing path to use.",
            S["body"]),
        sp(8),
    ]

    story += [
        step_box(1, "Operator uploads a document",
            "The operator taps Take Photo or Attach File. The app shows a preview screen "
            "with a green Attached badge, the file name and size, and an Upload and Sync button."),
        sp(6),
    ]

    # Upload flow table
    upload_rows = [
        [Paragraph("<b>State</b>", S["label"]),
         Paragraph("<b>What happens</b>", S["label"]),
         Paragraph("<b>What operator sees</b>", S["label"])],
        ["Online", "Image compressed, sent to backend, OCR runs, result returned",
         "3-step progress animation, then Result screen with risk score"],
        ["Offline", "Image saved to local SQLite as Pending status",
         "Snackbar: Saved as pending, auto-syncs when connected"],
        ["After sync", "Backend processes, result pushed to web dashboard via WebSocket",
         "Scan tile updates: Scanned -> Synced -> Reviewed"],
        ["Approved", "Manager clicks Approve in dashboard, FCM push sent",
         "Push notification: Declaration Approved"],
        ["Rejected", "Manager clicks Reject with note, FCM push sent",
         "Push notification: Declaration Rejected + manager note"],
    ]
    story.append(Table(upload_rows, colWidths=["18%","44%","38%"], style=TableStyle([
        ("BOX",(0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",(0,0),(-1,-1), 0.3, BORDER),
        ("BACKGROUND",(0,0),(-1,0), DBLUE),
        ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, GRAY]),
        ("LEFTPADDING",(0,0),(-1,-1), 6),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("FONTSIZE",(0,0),(-1,-1), 8),
    ])))
    story += [sp(8)]

    story += [
        step_box(2, "Backend decides: PDF or Image?",
            "The very first thing the backend checks is whether the upload is a digital PDF "
            "or a photo/image. This determines which processing path to use.", DBLUE),
        sp(4),
    ]
    story.append(code_block([
        '<font color="#6C7086"># PDF base64 always starts with "JVBERi0" (= %PDF- in base64)</font>',
        '<font color="#6C7086"># JPEG starts with "/9j/"   PNG starts with "iVBORw"</font>',
        '',
        '<font color="#89B4FA">if</font> is_pdf(payload.image_b64):',
        '    <font color="#6C7086"># Path A: Digital PDF  extract text directly (no OCR)</font>',
        '    text = extract_pdf_text_direct(payload.image_b64)   <font color="#6C7086"># uses pypdf</font>',
        '    <font color="#89B4FA">if not</font> text:',
        '        <font color="#6C7086"># Scanned/image PDF  fall back to Tesseract</font>',
        '        images = decode_pdf_pages(payload.image_b64)',
        '        text = run_tesseract(preprocess(img)) <font color="#89B4FA">for</font> img <font color="#89B4FA">in</font> images',
        '<font color="#89B4FA">else</font>:',
        '    <font color="#6C7086"># Path B: Photo/image  smart preprocess then Tesseract</font>',
        '    text = run_tesseract(preprocess(decode_image(payload.image_b64)))',
    ]))
    story += [sp(8)]

    story += [
        step_box(3, "Smart image preprocessing",
            "Not all images need the same treatment. A clean digital image needs only "
            "grayscale conversion. A dark or blurry phone photo needs the full pipeline.", DBLUE),
        sp(4),
    ]
    preproc_rows = [
        [Paragraph("<b>Image type</b>", S["label"]),
         Paragraph("<b>White pixel ratio</b>", S["label"]),
         Paragraph("<b>Processing applied</b>", S["label"])],
        ["Clean digital image (PDF render)", "> 55% white pixels",
         "Grayscale only -- Tesseract reads it perfectly as-is"],
        ["Good phone photo (well-lit, flat)", "> 55% white",
         "Grayscale only -- good lighting means clean contrast"],
        ["Dark/noisy phone photo", "< 55% white",
         "Grayscale + Gaussian denoise + adaptive threshold + deskew"],
    ]
    story.append(Table(preproc_rows, colWidths=["30%","25%","45%"], style=TableStyle([
        ("BOX",(0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",(0,0),(-1,-1), 0.3, BORDER),
        ("BACKGROUND",(0,0),(-1,0), LBLUE),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, GRAY]),
        ("LEFTPADDING",(0,0),(-1,-1), 6),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("FONTSIZE",(0,0),(-1,-1), 8),
    ])))
    story += [sp(8)]

    story += [
        step_box(4, "Three supported document types",
            "FlashPort supports all three standard customs trade documents. "
            "Each has different fields -- the extractor knows which fields to expect per type.", DBLUE),
        sp(4),
    ]
    doc_rows = [
        [Paragraph("<b>Document</b>", S["label"]),
         Paragraph("<b>Key fields extracted</b>", S["label"]),
         Paragraph("<b>Invoice value?</b>", S["label"])],
        ["Commercial Invoice",
         "HS Code, Invoice Value, Container ID, Importer, Exporter, Net/Gross Weight, Vessel, Port",
         "YES -- USD/EUR amount"],
        ["Bill of Lading",
         "HS Code, Container ID, Importer, Exporter, Vessel, Port, Carton Count, Gross Weight",
         "NO -- B/L does not contain invoice value"],
        ["Packing List",
         "HS Code, Container ID, Importer, Exporter, Vessel, Port, Net/Gross Weight, Carton Count",
         "NO -- packing list does not contain invoice value"],
    ]
    story.append(Table(doc_rows, colWidths=["25%","55%","20%"], style=TableStyle([
        ("BOX",(0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",(0,0),(-1,-1), 0.3, BORDER),
        ("BACKGROUND",(0,0),(-1,0), DBLUE),
        ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, GRAY]),
        ("LEFTPADDING",(0,0),(-1,-1), 6),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("FONTSIZE",(0,0),(-1,-1), 8),
    ])))
    story += [sp(8)]

    story += [info_box(
        "NOTE: Missing invoice_value on Bill of Lading and Packing List is NOT an error -- "
        "those document types do not contain invoice values. The risk scorer accounts for "
        "this by document type so they are not penalised for this missing field.",
        LBLUE, BLUE), sp(8)]

    # Summary table
    story += [Paragraph("Complete System Summary", S["h2"]), hr(BLUE, 1)]
    summary_rows = [
        [Paragraph("<b>Component</b>", S["label"]),
         Paragraph("<b>Technology</b>", S["label"]),
         Paragraph("<b>What it does</b>", S["label"])],
        ["Mobile App",         "Flutter (Dart)",             "Offline-first capture, auto-sync, FCM notifications"],
        ["PDF Text Extraction","pypdf",                      "Reads digital PDF text layer directly -- no OCR needed"],
        ["Image Preprocessing","OpenCV (smart pipeline)",    "Grayscale only for clean images, full pipeline for noisy photos"],
        ["OCR Engine",         "Tesseract eng+ind",          "Converts preprocessed image to raw text"],
        ["Field Extraction 1", "spaCy NER (custom trained)", "11 entity types, 100% F1, English + Indonesian"],
        ["Field Extraction 2", "Python Regex fallback",      "Fills gaps from NER, handles table-merge OCR patterns"],
        ["Risk Scoring",       "XGBoost (300 trees)",        "89.5% CV accuracy, 16 features"],
        ["Explainability",     "SHAP TreeExplainer",         "Per-feature contribution shown as bar chart in dashboard"],
        ["Database",           "PostgreSQL 15",              "Stores declarations, images, audit trail, watchlist, rules"],
        ["Web Dashboard",      "React 18 + Tailwind CSS",    "9-page pro dashboard: approve/reject, CEISA, SLA, audit"],
        ["Push Notifications", "Firebase FCM HTTP v1",       "Approve/reject decisions + CEISA lane results"],
        ["CEISA Gateway",      "Mock FastAPI (Phase 1)",     "SP2-200 / SP2-412 / SP2-500 lane responses in English"],
    ]
    story.append(Table(summary_rows, colWidths=["22%","22%","56%"], style=TableStyle([
        ("BOX",(0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",(0,0),(-1,-1), 0.3, BORDER),
        ("BACKGROUND",(0,0),(-1,0), DBLUE),
        ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, GRAY]),
        ("LEFTPADDING",(0,0),(-1,-1), 6),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("FONTSIZE",(0,0),(-1,-1), 8),
    ])))
    story += [sp(10)]
    story.append(HRFlowable(width="100%", thickness=1, color=DBLUE))
    story.append(Paragraph(
        "FlashPort  -  AI Open Innovation Challenge 2026  -  Case 1: Cikarang Dry Port  -  "
        "Team Teknik Logistik  -  President University  -  June 2026",
        S["footer"]))

    doc.build(story)
    print(f"PDF generated  {OUT}")
    print(f"Size: {OUT.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    build()
