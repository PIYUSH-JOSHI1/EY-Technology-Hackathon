from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from datetime import datetime, timedelta
import io

class SanctionAgent:
    """Sanction Agent - Generates sanction letters"""
    
    def generate_pdf(self, customer_data):
        """Generate sanction letter PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#003366'),
            spaceAfter=12,
            alignment=1
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#003366'),
            spaceAfter=6
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        # Header
        elements.append(Paragraph("TATA CAPITAL LIMITED", title_style))
        elements.append(Paragraph("Personal Loan Sanction Letter", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Date and Reference
        today = datetime.now()
        elements.append(Paragraph(f"<b>Date:</b> {today.strftime('%d-%m-%Y')}", normal_style))
        elements.append(Paragraph(f"<b>Reference No:</b> TCL/PL/{customer_data.get('customer_id', 'XXXX')}/{today.strftime('%Y%m%d')}", normal_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Customer Details
        elements.append(Paragraph("<b>CUSTOMER DETAILS</b>", heading_style))
        customer_table_data = [
            ['Name', customer_data.get('name', 'N/A')],
            ['Customer ID', customer_data.get('customer_id', 'N/A')],
            ['Age', str(customer_data.get('age', 'N/A'))],
            ['City', customer_data.get('city', 'N/A')],
            ['Phone', customer_data.get('phone', 'N/A')],
            ['Email', customer_data.get('email', 'N/A')],
        ]
        
        customer_table = Table(customer_table_data, colWidths=[2*inch, 4*inch])
        customer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F0F7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(customer_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Loan Details
        elements.append(Paragraph("<b>LOAN DETAILS</b>", heading_style))
        loan_amount = customer_data.get('loan_amount', 0)
        interest_rate = 12.0
        tenure = 36
        
        # Calculate EMI
        monthly_rate = interest_rate / 100 / 12
        emi = (loan_amount * monthly_rate * (1 + monthly_rate) ** tenure) / ((1 + monthly_rate) ** tenure - 1)
        total_amount = emi * tenure
        
        loan_table_data = [
            ['Loan Amount', f"₹{loan_amount:,.2f}"],
            ['Interest Rate', f"{interest_rate}% p.a."],
            ['Tenure', f"{tenure} months"],
            ['Monthly EMI', f"₹{emi:,.2f}"],
            ['Total Amount Payable', f"₹{total_amount:,.2f}"],
            ['Credit Score', str(customer_data.get('credit_score', 'N/A'))],
        ]
        
        loan_table = Table(loan_table_data, colWidths=[2*inch, 4*inch])
        loan_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F0F7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(loan_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Terms and Conditions
        elements.append(Paragraph("<b>TERMS & CONDITIONS</b>", heading_style))
        terms_text = """
        1. This sanction letter is valid for 30 days from the date of issue.<br/>
        2. The loan is subject to satisfactory completion of all formalities and documentation.<br/>
        3. The interest rate is fixed for the entire tenure of the loan.<br/>
        4. Prepayment is allowed without any penalty.<br/>
        5. The borrower must maintain a minimum balance as per bank norms.<br/>
        6. All terms and conditions as per the loan agreement shall apply.
        """
        elements.append(Paragraph(terms_text, normal_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Signature
        elements.append(Paragraph("_" * 50, normal_style))
        elements.append(Paragraph("Authorized Signatory<br/>Tata Capital Limited", normal_style))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
