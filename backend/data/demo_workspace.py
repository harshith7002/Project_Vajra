import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

DEMO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "demo")

def generate_demo_files(doc_processor):
    os.makedirs(DEMO_DIR, exist_ok=True)
    
    # 1. Pump_Inspection_Report_07.pdf
    pdf_path_1 = os.path.join(DEMO_DIR, "Pump_Inspection_Report_07.pdf")
    if not os.path.exists(pdf_path_1):
        doc1 = SimpleDocTemplate(pdf_path_1, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0F172A'), spaceAfter=12)
        normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#334155'))
        bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontSize=10, leading=14, fontName='Helvetica-Bold', textColor=colors.HexColor('#0F172A'))

        story = [
            Paragraph("CONFIDENTIAL INDUSTRIAL INSPECTION REPORT", ParagraphStyle('H', parent=styles['Heading3'], textColor=colors.HexColor('#0284C7'))),
            Paragraph("Equipment Inspection Report #07 — Boiler Feedwater Pump B-102", title_style),
            Spacer(1, 10),
            Paragraph("<b>Date:</b> August 24, 2026 | <b>Inspector:</b> R. Sharma, Senior Diagnostics Specialist", normal_style),
            Paragraph("<b>Facility:</b> SRM/SIH Thermal Power Unit — Zone 4 High Pressure Loop", normal_style),
            Spacer(1, 14),
            Paragraph("1. Operational Baseline & Telemetry Data", ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#0F172A'))),
            Paragraph("Boiler Feedwater Pump B-102 underwent routine vibration analysis and thermal imaging following scheduled operational hour threshold (4,500 hours).", normal_style),
            Spacer(1, 8),
            Paragraph("<b>Vibration Analysis Findings:</b>", bold_style),
            Paragraph("Vibration level measured at <b>7.8 mm/s RMS</b> on drive-end bearing housing (B-102-BRG). This significantly exceeds the ISO 10816 Class II alert threshold of <b>4.5 mm/s RMS</b> and mandatory action threshold of 7.0 mm/s RMS.", normal_style),
            Spacer(1, 8),
            Paragraph("<b>Thermal Imaging & Cavitation Observations:</b>", bold_style),
            Paragraph("Thermal camera spectrum recorded temperature of 88.4°C on drive-end sleeve casing. Acoustic emissions detect clear cavitation spikes within impeller stage 2 due to restricted inlet flow at Suction Strainer ST-01.", normal_style),
            Spacer(1, 14),
            Paragraph("2. Criticality Assessment & Action Plan", ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#0F172A'))),
            Paragraph("<b>CRITICALITY RATING: HIGH (Category 2 Alert)</b>. Continued operation poses severe risk of catastrophic bearing seizure and impeller destruction. Mandatory maintenance clearance required immediately.", normal_style)
        ]
        doc1.build(story)

    # 2. SOP_Pump_Maintenance_2025.pdf
    pdf_path_2 = os.path.join(DEMO_DIR, "SOP_Pump_Maintenance_2025.pdf")
    if not os.path.exists(pdf_path_2):
        doc2 = SimpleDocTemplate(pdf_path_2, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        story2 = [
            Paragraph("STANDARD OPERATING PROCEDURE", ParagraphStyle('H', parent=styles['Heading3'], textColor=colors.HexColor('#166534'))),
            Paragraph("SOP-Pump-Maintenance-2025: High Vibration Overhaul Protocol", ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0F172A'))),
            Spacer(1, 10),
            Paragraph("<b>Document Ref:</b> SOP-PLANT-2025-V4 | <b>Effective Date:</b> Jan 15, 2025", ParagraphStyle('N', parent=styles['Normal'], fontSize=10)),
            Spacer(1, 14),
            Paragraph("Section 4.2 Emergency Overhaul Thresholds", ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12)),
            Paragraph("Whenever measured vibration on high pressure feedwater pumps exceeds <b>7.0 mm/s RMS</b>, maintenance engineers must immediately trigger a Category 2 Emergency Shutdown.", ParagraphStyle('N', parent=styles['Normal'], fontSize=10, leading=14)),
            Spacer(1, 10),
            Paragraph("Required Overhaul Steps:", ParagraphStyle('B', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold')),
            Paragraph("1. Obtain formal Maintenance Approval Note signed by Maintenance Lead.<br/>"
                      "2. Verify LOTO isolation on high pressure feedwater valves HV-104 and pump power unit.<br/>"
                      "3. Clean and backflush Suction Strainer ST-01.<br/>"
                      "4. Inspect sleeve bearing B-102-BRG for tolerance wear and replace sleeve if clearance > 0.15mm.", ParagraphStyle('N', parent=styles['Normal'], fontSize=10, leading=14))
        ]
        doc2.build(story2)

    # 3. Safety_Procedure_Plant_Zone4.pdf
    pdf_path_3 = os.path.join(DEMO_DIR, "Safety_Procedure_Plant_Zone4.pdf")
    if not os.path.exists(pdf_path_3):
        doc3 = SimpleDocTemplate(pdf_path_3, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        story3 = [
            Paragraph("ZONE 4 PLANT SAFETY INSTRUCTIONS", ParagraphStyle('H', parent=styles['Heading3'], textColor=colors.HexColor('#991B1B'))),
            Paragraph("Safety Procedure: High-Pressure System Isolation & LOTO", ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0F172A'))),
            Spacer(1, 10),
            Paragraph("<b>Scope:</b> Applies to all maintenance personnel operating in Zone 4 High Pressure Feedwater Loop.", ParagraphStyle('N', parent=styles['Normal'], fontSize=10)),
            Spacer(1, 14),
            Paragraph("Lockout / Tagout (LOTO) Mandatory Protocol", ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12)),
            Paragraph("Prior to opening any pump casing or valve housing in Zone 4, personnel must lock out Valve HV-104 and verify zero hydraulic line pressure on Transducer PT-208. Safety padlocks must remain locked until final clearance.", ParagraphStyle('N', parent=styles['Normal'], fontSize=10, leading=14))
        ]
        doc3.build(story3)

    # 4. P&ID_Feedwater_Pump_B102.png (Multimodal image file)
    img_path = os.path.join(DEMO_DIR, "PID_Feedwater_Pump_B102.png")
    if not os.path.exists(img_path):
        img = Image.new("RGB", (900, 600), color=(15, 23, 42)) # Charcoal background
        draw = ImageDraw.Draw(img)
        
        # Draw grid & technical diagram lines
        draw.rectangle([20, 20, 880, 580], outline=(51, 65, 85), width=2)
        draw.text((40, 30), "P&ID DIAGRAM — FEEDWATER PUMP B-102 & DOWNSTREAM PIPING LOOP", fill=(56, 189, 248))
        draw.text((40, 50), "SRM INDUSTRIAL ENERGY COMPLEX | REV 3.2", fill=(148, 163, 184))

        # Inlet manifold
        draw.rectangle([80, 260, 200, 340], outline=(16, 185, 129), width=3, fill=(6, 78, 59))
        draw.text((90, 290), "STRAINER\n  ST-01", fill=(255, 255, 255))
        
        # Line from strainer to pump
        draw.line([200, 300, 320, 300], fill=(56, 189, 248), width=5)
        
        # Pump B-102
        draw.ellipse([320, 240, 440, 360], outline=(245, 158, 11), width=4, fill=(120, 53, 15))
        draw.text((345, 290), "PUMP B-102", fill=(255, 255, 255))
        
        # Discharge line
        draw.line([440, 300, 560, 300], fill=(56, 189, 248), width=5)
        
        # Check Valve CV-102
        draw.polygon([(560, 270), (560, 330), (600, 300)], outline=(239, 68, 68), fill=(153, 27, 27))
        draw.polygon([(640, 270), (640, 330), (600, 300)], outline=(239, 68, 68), fill=(153, 27, 27))
        draw.line([600, 300, 600, 250], fill=(239, 68, 68), width=3)
        draw.text((565, 230), "CHECK VALVE\n    CV-102", fill=(239, 68, 68))
        
        # Line to PT-208 & HV-104
        draw.line([640, 300, 720, 300], fill=(56, 189, 248), width=5)
        
        # Pressure Transducer PT-208
        draw.line([720, 300, 720, 200], fill=(168, 85, 247), width=3)
        draw.ellipse([695, 150, 745, 200], outline=(168, 85, 247), width=3, fill=(88, 28, 135))
        draw.text((700, 170), "PT-208", fill=(255, 255, 255))
        
        # Isolation Valve HV-104
        draw.rectangle([760, 260, 840, 340], outline=(34, 197, 94), width=3, fill=(20, 83, 45))
        draw.text((770, 290), "VALVE\nHV-104", fill=(255, 255, 255))

        img.save(img_path)

    # Ingest into document processor
    for fname in ["Pump_Inspection_Report_07.pdf", "SOP_Pump_Maintenance_2025.pdf", "Safety_Procedure_Plant_Zone4.pdf", "PID_Feedwater_Pump_B102.png"]:
        fpath = os.path.join(DEMO_DIR, fname)
        if os.path.exists(fpath):
            doc_record = doc_processor.process_file(fpath, fname)
            from backend.rag.engine import rag_engine
            rag_engine.index_chunks(doc_record["chunks"])
