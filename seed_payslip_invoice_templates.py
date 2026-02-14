"""
Seed payslip and invoice HTML templates into the database.
Run: python seed_payslip_invoice_templates.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.template import Template, TemplateType

PAYSLIP_TEMPLATE = """
<div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 800px; margin: 0 auto; color: #111;">

  <!-- Header -->
  <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
    <div>
      <p style="font-size: 11px; color: #666; margin: 4px 0;">Reference</p>
      <p style="font-size: 13px; font-weight: bold; margin: 2px 0;">{{reference}}</p>
      <p style="font-size: 11px; color: #666; margin: 4px 0;">Pay Date</p>
      <p style="font-size: 13px; font-weight: bold; margin: 2px 0;">{{pay_date}}</p>
      <p style="font-size: 11px; color: #666; margin: 4px 0;">Pay Period</p>
      <p style="font-size: 13px; font-weight: bold; margin: 2px 0;">{{pay_period}}</p>
    </div>
    <div style="text-align: right;">
      <h1 style="font-size: 28px; color: #FF6B00; margin: 0;">Payslip</h1>
    </div>
  </div>

  <hr style="border: none; border-top: 2px solid #FF6B00; margin: 16px 0;" />

  <!-- Employee & Employer Details -->
  <div style="display: flex; justify-content: space-between; margin-bottom: 24px;">
    <div>
      <p style="font-size: 12px; color: #FF6B00; font-weight: bold; margin-bottom: 4px;">Employee Details</p>
      <p style="font-size: 14px; font-weight: bold; margin: 2px 0;">{{contractor_name}}</p>
      <p style="font-size: 12px; color: #666; margin: 2px 0;">{{client_name}}</p>
      <p style="font-size: 12px; color: #666; margin: 2px 0;">{{position}}</p>
    </div>
    <div style="text-align: right;">
      <p style="font-size: 12px; color: #FF6B00; font-weight: bold; margin-bottom: 4px;">Employer Details</p>
      <p style="font-size: 14px; font-weight: bold; margin: 2px 0;">Aventus Talent Consultancy LLC</p>
      <p style="font-size: 12px; color: #666; margin: 2px 0;">Office 14, Golden Mile 4,</p>
      <p style="font-size: 12px; color: #666; margin: 2px 0;">Palm Jumeirah, Dubai, UAE</p>
    </div>
  </div>

  <!-- Earnings -->
  <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <thead>
      <tr style="background: #FF6B00;">
        <th style="text-align: left; padding: 8px 10px; color: white; font-size: 13px;">Earnings</th>
        <th style="text-align: right; padding: 8px 10px; color: white; font-size: 13px;">Amount</th>
      </tr>
    </thead>
    <tbody>
      <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 8px 10px; font-size: 12px; color: #333;">Basic Pay (50%)</td>
        <td style="padding: 8px 10px; font-size: 12px; font-weight: bold; text-align: right;">{{currency}} {{basic_pay}}</td>
      </tr>
      <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 8px 10px; font-size: 12px; color: #333;">Housing Allowance (25%)</td>
        <td style="padding: 8px 10px; font-size: 12px; font-weight: bold; text-align: right;">{{currency}} {{housing_allowance}}</td>
      </tr>
      <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 8px 10px; font-size: 12px; color: #333;">Transport Allowance (16.67%)</td>
        <td style="padding: 8px 10px; font-size: 12px; font-weight: bold; text-align: right;">{{currency}} {{transport_allowance}}</td>
      </tr>
      <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 8px 10px; font-size: 12px; color: #333;">Leave Allowance</td>
        <td style="padding: 8px 10px; font-size: 12px; font-weight: bold; text-align: right;">{{currency}} {{leave_allowance}}</td>
      </tr>
    </tbody>
  </table>

  <!-- Deductions -->
  <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <thead>
      <tr style="background: #FFF0E6;">
        <th style="text-align: left; padding: 8px 10px; color: #CC5500; font-size: 13px;">Deductions</th>
        <th style="text-align: right; padding: 8px 10px; color: #CC5500; font-size: 13px;">Amount</th>
      </tr>
    </thead>
    <tbody>
      <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 8px 10px; font-size: 12px; color: #333;">Expenses Reimbursement</td>
        <td style="padding: 8px 10px; font-size: 12px; font-weight: bold; text-align: right;">+{{currency}} {{expenses_reimbursement}}</td>
      </tr>
      <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 8px 10px; font-size: 12px; color: #333;">Leave Deductions</td>
        <td style="padding: 8px 10px; font-size: 12px; font-weight: bold; text-align: right;">-{{currency}} {{leave_deductions}}</td>
      </tr>
    </tbody>
  </table>

  <!-- Total Pay -->
  <table style="width: 100%; border-collapse: collapse; margin-bottom: 8px;">
    <tr style="background: #FF6B00;">
      <td style="padding: 10px; color: white; font-size: 15px; font-weight: bold;">Total Pay</td>
      <td style="padding: 10px; color: white; font-size: 15px; font-weight: bold; text-align: right;">{{currency}} {{net_salary}}</td>
    </tr>
  </table>
  <div style="background: #f8f8f8; border: 1px solid #ddd; padding: 8px 10px; margin-bottom: 24px;">
    <span style="font-size: 12px; font-weight: bold; color: #333;">Total Pay in Words:</span>
    <span style="font-size: 12px; font-style: italic; color: #333;"> {{net_salary_in_words}}</span>
  </div>

  <!-- Payment Details -->
  <div style="margin-bottom: 24px;">
    <p style="font-size: 12px; color: #FF6B00; font-weight: bold; margin-bottom: 4px;">Payment Details</p>
    <p style="font-size: 12px; color: #666;">Payment made to employee's bank account.</p>
    <p style="font-size: 12px; color: #666;">Bank: {{bank_name}} | IBAN: {{iban}}</p>
  </div>

  <!-- Signatures -->
  <div style="display: flex; justify-content: space-between; margin-top: 40px;">
    <div>
      <p style="font-size: 12px; font-weight: bold; color: #333; margin-bottom: 40px;">Employee Signature</p>
      <p style="border-top: 1px solid #333; padding-top: 4px; font-size: 11px; color: #666;">{{contractor_name}}</p>
    </div>
    <div style="text-align: right;">
      <p style="font-size: 12px; font-weight: bold; color: #333; margin-bottom: 40px;">Employer Signature</p>
      <p style="border-top: 1px solid #333; padding-top: 4px; font-size: 11px; color: #666;">Aventus Talent Consultancy LLC</p>
    </div>
  </div>

  <!-- Footer -->
  <div style="margin-top: 32px; padding-top: 12px; border-top: 1px solid #ddd;">
    <p style="font-size: 9px; color: #999; text-align: center;">
      This payslip is computer-generated and does not require a physical signature.
      For queries, contact payroll@aventus-talent.com
    </p>
  </div>
</div>
"""

INVOICE_TEMPLATE = """
<div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 800px; margin: 0 auto; color: #111;">

  <!-- Header -->
  <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
    <div>
      <p style="font-size: 11px; color: #666; margin: 4px 0;">Invoice Number</p>
      <p style="font-size: 13px; font-weight: bold; margin: 2px 0;">{{invoice_number}}</p>
      <p style="font-size: 11px; color: #666; margin: 4px 0;">Invoice Date</p>
      <p style="font-size: 13px; font-weight: bold; margin: 2px 0;">{{invoice_date}}</p>
      <p style="font-size: 11px; color: #666; margin: 4px 0;">Period</p>
      <p style="font-size: 13px; font-weight: bold; margin: 2px 0;">{{period}}</p>
      <p style="font-size: 11px; color: #666; margin: 4px 0;">Payment Terms</p>
      <p style="font-size: 13px; font-weight: bold; margin: 2px 0;">{{payment_terms}}</p>
    </div>
    <div style="text-align: right;">
      <h1 style="font-size: 28px; color: #FF6B00; margin: 0;">Invoice</h1>
    </div>
  </div>

  <hr style="border: none; border-top: 2px solid #FF6B00; margin: 16px 0;" />

  <!-- From & Bill To -->
  <div style="display: flex; justify-content: space-between; margin-bottom: 24px;">
    <div>
      <p style="font-size: 12px; color: #FF6B00; font-weight: bold; margin-bottom: 4px;">From</p>
      <p style="font-size: 14px; font-weight: bold; margin: 2px 0;">Aventus Talent Consultancy LLC</p>
      <p style="font-size: 12px; color: #666; margin: 2px 0;">Office 14, Golden Mile 4,</p>
      <p style="font-size: 12px; color: #666; margin: 2px 0;">Palm Jumeirah, Dubai, UAE</p>
      <p style="font-size: 12px; color: #666; margin: 2px 0;">TRN: {{company_trn}}</p>
    </div>
    <div style="text-align: right;">
      <p style="font-size: 12px; color: #FF6B00; font-weight: bold; margin-bottom: 4px;">Bill To</p>
      <p style="font-size: 14px; font-weight: bold; margin: 2px 0;">{{client_name}}</p>
      <p style="font-size: 12px; color: #666; margin: 2px 0;">{{client_address_line1}}</p>
      <p style="font-size: 12px; color: #666; margin: 2px 0;">{{client_address_line2}}</p>
      <p style="font-size: 12px; color: #666; margin: 2px 0;">{{client_country}}</p>
    </div>
  </div>

  <!-- Service Details -->
  <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <thead>
      <tr style="background: #FF6B00;">
        <th style="text-align: left; padding: 8px 10px; color: white; font-size: 13px;">Description</th>
        <th style="text-align: right; padding: 8px 10px; color: white; font-size: 13px;">Amount</th>
      </tr>
    </thead>
    <tbody>
      <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 8px 10px; font-size: 12px; color: #333;">
          Contractor Services - {{contractor_name}}<br/>
          <span style="font-size: 11px; color: #666;">Period: {{period}}</span>
        </td>
        <td style="padding: 8px 10px; font-size: 12px; font-weight: bold; text-align: right;">{{currency}} {{net_salary}}</td>
      </tr>
      <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 8px 10px; font-size: 12px; color: #333;">Third Party Accruals</td>
        <td style="padding: 8px 10px; font-size: 12px; font-weight: bold; text-align: right;">{{currency}} {{total_accruals}}</td>
      </tr>
      <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 8px 10px; font-size: 12px; color: #333;">Management Fee</td>
        <td style="padding: 8px 10px; font-size: 12px; font-weight: bold; text-align: right;">{{currency}} {{management_fee}}</td>
      </tr>
    </tbody>
  </table>

  <!-- Totals -->
  <table style="width: 50%; margin-left: auto; border-collapse: collapse; margin-bottom: 8px;">
    <tr style="border-bottom: 1px solid #eee;">
      <td style="padding: 6px 10px; font-size: 12px; color: #333;">Subtotal</td>
      <td style="padding: 6px 10px; font-size: 12px; font-weight: bold; text-align: right;">{{currency}} {{subtotal}}</td>
    </tr>
    <tr style="border-bottom: 1px solid #eee;">
      <td style="padding: 6px 10px; font-size: 12px; color: #333;">VAT ({{vat_rate_percent}})</td>
      <td style="padding: 6px 10px; font-size: 12px; font-weight: bold; text-align: right;">{{currency}} {{vat_amount}}</td>
    </tr>
  </table>
  <table style="width: 50%; margin-left: auto; border-collapse: collapse; margin-bottom: 24px;">
    <tr style="background: #FF6B00;">
      <td style="padding: 10px; color: white; font-size: 14px; font-weight: bold;">Total Due</td>
      <td style="padding: 10px; color: white; font-size: 14px; font-weight: bold; text-align: right;">{{currency}} {{total_payable}}</td>
    </tr>
  </table>

  <!-- Payment Terms -->
  <div style="margin-bottom: 24px;">
    <p style="font-size: 12px; color: #FF6B00; font-weight: bold; margin-bottom: 4px;">Payment Terms</p>
    <p style="font-size: 12px; color: #666;">Payment is due within {{payment_terms}} of invoice date.</p>
    <p style="font-size: 12px; color: #666;">Due Date: {{due_date}}</p>
  </div>

  <!-- Bank Details -->
  <div style="margin-bottom: 24px;">
    <p style="font-size: 12px; color: #FF6B00; font-weight: bold; margin-bottom: 8px;">Bank Details</p>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
      <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 6px 10px; font-size: 12px; color: #666; width: 35%; background: #f8f8f8; font-weight: bold;">Bank Name</td>
        <td style="padding: 6px 10px; font-size: 12px;">Emirates NBD</td>
      </tr>
      <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 6px 10px; font-size: 12px; color: #666; background: #f8f8f8; font-weight: bold;">Account Name</td>
        <td style="padding: 6px 10px; font-size: 12px;">Aventus Talent Consultancy LLC</td>
      </tr>
      <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 6px 10px; font-size: 12px; color: #666; background: #f8f8f8; font-weight: bold;">IBAN</td>
        <td style="padding: 6px 10px; font-size: 12px;">AE12 3456 7890 1234 5678 901</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 12px; color: #666; background: #f8f8f8; font-weight: bold;">SWIFT / BIC</td>
        <td style="padding: 6px 10px; font-size: 12px;">EBILORAE</td>
      </tr>
    </table>
  </div>

  <!-- Footer -->
  <div style="margin-top: 32px; padding-top: 12px; border-top: 1px solid #ddd; text-align: center;">
    <p style="font-size: 13px; color: #FF6B00; font-weight: bold;">Thank you for your business</p>
    <p style="font-size: 9px; color: #999; margin-top: 8px;">
      This invoice is computer-generated. For queries, contact finance@aventus-talent.com
    </p>
  </div>
</div>
"""


def seed():
    db = SessionLocal()
    try:
        # Check if templates already exist
        existing_payslip = db.query(Template).filter(
            Template.template_type == TemplateType.PAYSLIP.value
        ).first()
        existing_invoice = db.query(Template).filter(
            Template.template_type == TemplateType.INVOICE.value
        ).first()

        created = []

        if not existing_payslip:
            payslip = Template(
                name="Standard Payslip",
                template_type=TemplateType.PAYSLIP.value,
                description="Default payslip template with earnings, deductions, payment details and signatures.",
                content=PAYSLIP_TEMPLATE.strip(),
                is_active=True,
            )
            db.add(payslip)
            created.append("Payslip")
            print("Created: Standard Payslip template")
        else:
            print("Skipped: Payslip template already exists")

        if not existing_invoice:
            invoice = Template(
                name="Standard Invoice",
                template_type=TemplateType.INVOICE.value,
                description="Default client invoice template with service details, VAT breakdown and bank details.",
                content=INVOICE_TEMPLATE.strip(),
                is_active=True,
            )
            db.add(invoice)
            created.append("Invoice")
            print("Created: Standard Invoice template")
        else:
            print("Skipped: Invoice template already exists")

        if created:
            db.commit()
            print(f"\nDone! Created {len(created)} template(s): {', '.join(created)}")
        else:
            print("\nNo new templates needed.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
