import os
import csv
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_sample_pdf(pdf_path: str):
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'DocHeader',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#475569'),
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=8
    )

    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#dc2626'),
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # Page 1: FIR 104/2026 (New Delhi)
    story.append(Paragraph("CONFIDENTIAL // LAW ENFORCEMENT INTELLIGENCE CASE DOSSIER", badge_style))
    story.append(Paragraph("FIRST INFORMATION REPORT (FIR NO: 104/2026)", title_style))
    story.append(Paragraph("<b>Police Station:</b> Cyber Crime & Special Operations, New Delhi | <b>Date:</b> 04-AUG-2026 | <b>Section:</b> IPC 370, 420, 120B / IT Act 66D", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=10))
    story.append(Paragraph(
        "<b>Case Summary:</b> Acting upon intercepted communications and intelligence inputs from the NCRB Cyber Intelligence Cell, "
        "a coordinated investigation was initiated against an interstate organized crime syndicate. Primary suspect "
        "<b>Vikram Singh</b> (contact: <b>+919876543210</b>) has been identified as operating an extortion and illegal human trafficking pipeline "
        "spanning Delhi NCR and Uttar Pradesh. Informant accounts reveal Vikram Singh coordinates safehouses and transit logistics through his key lieutenant "
        "<b>Amit Sharma</b> (contact: <b>+919811122334</b>).", body_style))
    story.append(Paragraph(
        "Surveillance indicates Amit Sharma manages transport vehicles registered under alias entities, specifically a white SUV registration "
        "<b>DL-01-AB-1234</b>. Financial proceeds from trafficking victims are routed through shell banking conduits controlled by "
        "<b>Sunita Rao</b> (contact: <b>+919822233445</b>). On 02-AUG-2026, Amit Sharma was recorded meeting courier <b>Dinesh Verma</b> "
        "near Connaught Place, New Delhi, handing over forged identity certificates and travel clearance manifests.", body_style))
    story.append(Paragraph("<b>Key Entities Tagged:</b> Vikram Singh, Amit Sharma, Sunita Rao, Dinesh Verma, DL-01-AB-1234, New Delhi", header_style))
    story.append(Spacer(1, 30))

    # Page 2: FIR 88/2026 (Noida)
    story.append(Paragraph("FIRST INFORMATION REPORT (FIR NO: 88/2026)", title_style))
    story.append(Paragraph("<b>Police Station:</b> Sector 18 Police Station, Gautam Buddha Nagar, Noida | <b>Date:</b> 08-AUG-2026 | <b>Section:</b> IPC 406, 420, 468", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=10))
    story.append(Paragraph(
        "<b>Case Summary:</b> Complaint filed by commercial audit vigilance regarding suspicious financial layering executed via "
        "<b>Apex Logistics Pvt Ltd</b>, registered under managing director <b>Rajan Malhotra</b> (contact: <b>+919844455667</b>). "
        "Investigation reveals Apex Logistics functioned as a corporate front for laundering illicit cash flows originating from syndicate operations.", body_style))
    story.append(Paragraph(
        "Financial analysis corroborates multiple high-value RTGS transfers dispatched to bank accounts operated by <b>Sunita Rao</b>. "
        "Ground intel confirms logistics dispatch vehicle <b>UP-32-CD-5678</b>, registered to Dinesh Verma, was intercepted transporting "
        "unaccounted cash packets between Noida Sector 62 and safehouses in Rohini, Delhi. Technical intercepts establish direct voice calls between "
        "Rajan Malhotra and Vikram Singh arranging international transit clearances.", body_style))
    story.append(Paragraph("<b>Key Entities Tagged:</b> Rajan Malhotra, Sunita Rao, Dinesh Verma, Vikram Singh, UP-32-CD-5678, Apex Logistics, Noida", header_style))
    story.append(Spacer(1, 30))

    # Page 3: FIR 212/2026 (Lucknow)
    story.append(Paragraph("FIRST INFORMATION REPORT (FIR NO: 212/2026)", title_style))
    story.append(Paragraph("<b>Police Station:</b> Gomti Nagar PS, Lucknow Commissionerate | <b>Date:</b> 12-AUG-2026 | <b>Section:</b> IPC 370(2), 34, 120B", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=10))
    story.append(Paragraph(
        "<b>Case Summary:</b> Following a midnight highway patrol check near Shaheed Path, Lucknow, police units intercepted a utility vehicle "
        "bearing registration <b>UP-32-CD-5678</b> driven by <b>Dinesh Verma</b> (+919833344556). Inside the vehicle, officers recovered "
        "forged travel manifests, twelve mobile handsets, and ledgers documenting financial settlements with <b>Kabir Khan</b> "
        "(contact: <b>+919877788990</b>), a border transit operative based in Kolkata.", body_style))
    story.append(Paragraph(
        "During interrogation, Dinesh Verma revealed he operated on instructions issued directly by Vikram Singh and Amit Sharma. "
        "The transit vehicle DL-01-AB-1234 was identified as having rendezvoused with UP-32-CD-5678 on 11-AUG-2026 to exchange logistical supplies.", body_style))
    story.append(Paragraph("<b>Key Entities Tagged:</b> Dinesh Verma, Vikram Singh, Amit Sharma, Kabir Khan, UP-32-CD-5678, DL-01-AB-1234, Lucknow, Kolkata", header_style))
    story.append(Spacer(1, 30))

    # Page 4: Surveillance Report SR-409
    story.append(Paragraph("INTELLIGENCE SURVEILLANCE REPORT (SR-409)", title_style))
    story.append(Paragraph("<b>Agency:</b> Central Field Intelligence Detachment | <b>Classification:</b> SECRET // REL TO CASE SIH26189 | <b>Date:</b> 14-AUG-2026", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=10))
    story.append(Paragraph(
        "<b>Surveillance Overview:</b> Field agents maintained round-the-clock physical and electronic monitoring of target subject Vikram Singh "
        "at Hotel Grand, Connaught Place, New Delhi. Between 01:30 AM and 03:45 AM on consecutive nights (11-AUG to 14-AUG-2026), unusual high-density "
        "cellular activity was detected. Vikram Singh placed multiple urgent encrypted calls to Dinesh Verma and Sunita Rao.", body_style))
    story.append(Paragraph(
        "At 02:15 AM on 13-AUG-2026, courier Dinesh Verma arrived in vehicle DL-01-AB-1234 and delivered a locked briefcase to Vikram Singh. "
        "Subject Amit Sharma was present and instructed courier Dinesh to deliver documents to <b>Priya Kapoor</b> (contact: <b>+919866677889</b>) "
        "for expedited visa facilitation in Gurugram.", body_style))
    story.append(Paragraph("<b>Key Entities Tagged:</b> Vikram Singh, Dinesh Verma, Amit Sharma, Sunita Rao, Priya Kapoor, DL-01-AB-1234, Connaught Place, Gurugram", header_style))
    story.append(Spacer(1, 30))

    # Page 5: Social Media Intelligence Note SM-88
    story.append(Paragraph("OPEN SOURCE & SOCIAL MEDIA INTELLIGENCE NOTE (SM-88)", title_style))
    story.append(Paragraph("<b>Unit:</b> Cyber Threat Intelligence Unit | <b>Platform:</b> Telegram / Encrypted Channels | <b>Date:</b> 16-AUG-2026", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=10))
    story.append(Paragraph(
        "<b>Intelligence Summary:</b> Technical monitoring of recruitment networks flagged Telegram handle '@SkylineOps' operated by "
        "<b>Neha Saxena</b> (contact: <b>+919855566778</b>). The channel advertised overseas placement opportunities targeting vulnerable women, "
        "promising hotel hospitality employment in Southeast Asia.", body_style))
    story.append(Paragraph(
        "Financial escrow for these operations was linked directly to UPI accounts maintained by Sunita Rao. "
        "Recruits were directed to report to safehouse centers in Kolkata managed by Kabir Khan before final transit routing. "
        "Direct link identified between Neha Saxena, Rajan Malhotra (Apex Logistics), and syndicate head Vikram Singh.", body_style))
    story.append(Paragraph("<b>Key Entities Tagged:</b> Neha Saxena, Sunita Rao, Kabir Khan, Rajan Malhotra, Vikram Singh, Kolkata, Mumbai", header_style))

    doc.build(story)
    print(f"Created PDF report: {pdf_path}")

def create_sample_cdr(csv_path: str):
    # 16 records with deliberate odd-hour calls (1-4 AM) and tower locations
    cdr_rows = [
        # record_id, caller_number, caller_name, receiver_number, receiver_name, timestamp, duration_sec, tower_location
        ("CDR-0001", "+919876543210", "Vikram Singh", "+919811122334", "Amit Sharma", "2026-08-10 10:14:22", 340, "Connaught Place, New Delhi"),
        ("CDR-0002", "+919811122334", "Amit Sharma", "+919833344556", "Dinesh Verma", "2026-08-10 11:32:05", 185, "Rohini Sector 7, New Delhi"),
        ("CDR-0003", "+919876543210", "Vikram Singh", "+919822233445", "Sunita Rao", "2026-08-11 14:05:19", 520, "Connaught Place, New Delhi"),
        ("CDR-0004", "+919876543210", "Vikram Singh", "+919833344556", "Dinesh Verma", "2026-08-12 02:15:40", 410, "Connaught Place, New Delhi"), # Odd hour
        ("CDR-0005", "+919833344556", "Dinesh Verma", "+919876543210", "Vikram Singh", "2026-08-12 02:45:11", 195, "Noida Sector 62, Noida"),     # Odd hour
        ("CDR-0006", "+919822233445", "Sunita Rao", "+919844455667", "Rajan Malhotra", "2026-08-12 16:22:45", 290, "Lajpat Nagar, New Delhi"),
        ("CDR-0007", "+919844455667", "Rajan Malhotra", "+919876543210", "Vikram Singh", "2026-08-13 01:45:30", 380, "Noida Sector 18, Noida"),      # Odd hour
        ("CDR-0008", "+919876543210", "Vikram Singh", "+919877788990", "Kabir Khan", "2026-08-13 03:10:15", 620, "Connaught Place, New Delhi"),  # Odd hour
        ("CDR-0009", "+919877788990", "Kabir Khan", "+919833344556", "Dinesh Verma", "2026-08-13 03:40:55", 145, "Salt Lake City, Kolkata"),   # Odd hour
        ("CDR-0010", "+919811122334", "Amit Sharma", "+919866677889", "Priya Kapoor", "2026-08-13 09:20:10", 215, "Cyber City, Gurugram"),
        ("CDR-0011", "+919855566778", "Neha Saxena", "+919822233445", "Sunita Rao", "2026-08-14 11:15:33", 480, "Bandra West, Mumbai"),
        ("CDR-0012", "+919855566778", "Neha Saxena", "+919877788990", "Kabir Khan", "2026-08-14 15:50:12", 360, "Bandra West, Mumbai"),
        ("CDR-0013", "+919833344556", "Dinesh Verma", "+919811122334", "Amit Sharma", "2026-08-15 02:30:18", 175, "Gomti Nagar, Lucknow"),       # Odd hour
        ("CDR-0014", "+919876543210", "Vikram Singh", "+919855566778", "Neha Saxena", "2026-08-15 18:40:02", 510, "Connaught Place, New Delhi"),
        ("CDR-0015", "+919844455667", "Rajan Malhotra", "+919833344556", "Dinesh Verma", "2026-08-16 12:05:44", 260, "Noida Sector 18, Noida"),
        ("CDR-0016", "+919866677889", "Priya Kapoor", "+919876543210", "Vikram Singh", "2026-08-16 20:11:59", 310, "Cyber City, Gurugram"),
    ]

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["record_id", "caller_number", "caller_name", "receiver_number", "receiver_name", "timestamp", "duration_sec", "tower_location"])
        writer.writerows(cdr_rows)
    print(f"Created CDR CSV: {csv_path}")

def create_sample_txn(xlsx_path: str):
    txn_rows = [
        {"txn_id": "TXN-1001", "from_account": "AC-778899005", "from_name": "Rajan Malhotra (Apex Logistics)", "to_account": "AC-778899003", "to_name": "Sunita Rao", "amount": 1850000.0, "mode": "RTGS", "date": "2026-08-11 10:15:00", "remarks": "Consultancy vendor invoice settlement"},
        {"txn_id": "TXN-1002", "from_account": "AC-778899003", "from_name": "Sunita Rao", "to_account": "CASH-BRANCH-01", "to_name": "Self (Cash Withdrawal)", "amount": 450000.0, "mode": "CASH", "date": "2026-08-11 11:30:00", "remarks": "Urgent cash withdrawal same day post RTGS"}, # Anomaly
        {"txn_id": "TXN-1003", "from_account": "AC-778899003", "from_name": "Sunita Rao", "to_account": "CASH-BRANCH-02", "to_name": "Self (Cash Withdrawal)", "amount": 490000.0, "mode": "CASH", "date": "2026-08-11 13:45:00", "remarks": "Second cash withdrawal below 5L threshold"},     # Anomaly
        {"txn_id": "TXN-1004", "from_account": "AC-778899003", "from_name": "Sunita Rao", "to_account": "CASH-BRANCH-03", "to_name": "Self (Cash Withdrawal)", "amount": 500000.0, "mode": "CASH", "date": "2026-08-11 16:10:00", "remarks": "Third cash withdrawal same day"},             # Anomaly
        {"txn_id": "TXN-1005", "from_account": "AC-778899003", "from_name": "Sunita Rao", "to_account": "AC-778899001", "to_name": "Vikram Singh", "amount": 350000.0, "mode": "IMPS", "date": "2026-08-12 09:30:00", "remarks": "Operational fee remittance"},
        {"txn_id": "TXN-1006", "from_account": "AC-778899001", "from_name": "Vikram Singh", "to_account": "AC-778899002", "to_name": "Amit Sharma", "amount": 125000.0, "mode": "IMPS", "date": "2026-08-12 11:45:00", "remarks": "Safehouse rent and fleet maintenance"},
        {"txn_id": "TXN-1007", "from_account": "AC-778899002", "from_name": "Amit Sharma", "to_account": "AC-778899004", "to_name": "Dinesh Verma", "amount": 48000.0, "mode": "UPI", "date": "2026-08-12 14:10:00", "remarks": "Driver transit fuel allowance"}, # Structured < 50k
        {"txn_id": "TXN-1008", "from_account": "AC-778899002", "from_name": "Amit Sharma", "to_account": "AC-778899004", "to_name": "Dinesh Verma", "amount": 49500.0, "mode": "UPI", "date": "2026-08-12 14:15:00", "remarks": "Highway toll emergency fund"},    # Structured < 50k
        {"txn_id": "TXN-1009", "from_account": "AC-778899002", "from_name": "Amit Sharma", "to_account": "AC-778899004", "to_name": "Dinesh Verma", "amount": 49000.0, "mode": "UPI", "date": "2026-08-12 14:20:00", "remarks": "Vehicle repair settlement"},        # Structured < 50k
        {"txn_id": "TXN-1010", "from_account": "AC-778899005", "from_name": "Rajan Malhotra (Apex Logistics)", "to_account": "AC-778899008", "to_name": "Kabir Khan", "amount": 750000.0, "mode": "RTGS", "date": "2026-08-13 10:00:00", "remarks": "Eastern sector transport contract"},
        {"txn_id": "TXN-1011", "from_account": "AC-778899006", "from_name": "Neha Saxena", "to_account": "AC-778899003", "to_name": "Sunita Rao", "amount": 280000.0, "mode": "NEFT", "date": "2026-08-14 12:20:00", "remarks": "Candidate security deposits"},
        {"txn_id": "TXN-1012", "from_account": "AC-778899001", "from_name": "Vikram Singh", "to_account": "AC-778899007", "to_name": "Priya Kapoor", "amount": 95000.0, "mode": "IMPS", "date": "2026-08-14 17:40:00", "remarks": "Document certification fees"},
        {"txn_id": "TXN-1013", "from_account": "AC-778899008", "from_name": "Kabir Khan", "to_account": "AC-778899004", "to_name": "Dinesh Verma", "amount": 65000.0, "mode": "IMPS", "date": "2026-08-15 08:30:00", "remarks": "Border clearance coordination"},
        {"txn_id": "TXN-1014", "from_account": "AC-778899005", "from_name": "Rajan Malhotra (Apex Logistics)", "to_account": "AC-778899001", "to_name": "Vikram Singh", "amount": 500000.0, "mode": "RTGS", "date": "2026-08-15 16:50:00", "remarks": "Management retained dividend"},
        {"txn_id": "TXN-1015", "from_account": "AC-778899007", "from_name": "Priya Kapoor", "to_account": "AC-778899002", "to_name": "Amit Sharma", "amount": 40000.0, "mode": "UPI", "date": "2026-08-16 11:10:00", "remarks": "Express courier processing fee"},
    ]

    df = pd.DataFrame(txn_rows)
    df.to_excel(xlsx_path, index=False)
    print(f"Created Transactions XLSX: {xlsx_path}")

if __name__ == "__main__":
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sample_dirs = [
        os.path.join(workspace_dir, "sample_data"),
        os.path.join(workspace_dir, "backend", "sample_data")
    ]
    
    for s_dir in sample_dirs:
        os.makedirs(s_dir, exist_ok=True)
        pdf_f = os.path.join(s_dir, "sample_unstructured_reports.pdf")
        csv_f = os.path.join(s_dir, "sample_cdr_data.csv")
        xlsx_f = os.path.join(s_dir, "sample_financial_transactions.xlsx")
        
        create_sample_pdf(pdf_f)
        create_sample_cdr(csv_f)
        create_sample_txn(xlsx_f)
    print("All sample data generated successfully!")
