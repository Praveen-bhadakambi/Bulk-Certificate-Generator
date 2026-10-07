from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from app.config import CERTIFICATE_DIR


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return cleaned.strip("_") or "certificate"


def generate_certificate_pdf(
    *,
    job_id: int,
    certificate_id: int,
    recipient_name: str,
    course_name: str,
    issuer_name: str,
    issue_date: str,
    event_name: str | None = None,
    custom_message: str | None = None,
) -> Path:
    if recipient_name.strip().lower() == "fail generation":
        raise RuntimeError("Simulated certificate generation failure")

    job_dir = CERTIFICATE_DIR / str(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    output_path = job_dir / f"{certificate_id}_{_safe_filename(recipient_name)}.pdf"

    page_width, page_height = landscape(A4)
    pdf = canvas.Canvas(str(output_path), pagesize=landscape(A4))

    margin = 0.55 * inch
    pdf.setStrokeColor(colors.HexColor("#1F2937"))
    pdf.setLineWidth(3)
    pdf.rect(margin, margin, page_width - 2 * margin, page_height - 2 * margin)

    pdf.setStrokeColor(colors.HexColor("#C8A24A"))
    pdf.setLineWidth(1.5)
    pdf.rect(margin + 12, margin + 12, page_width - 2 * (margin + 12), page_height - 2 * (margin + 12))

    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.setFont("Times-Bold", 34)
    pdf.drawCentredString(page_width / 2, page_height - 1.45 * inch, "Certificate of Completion")

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(page_width / 2, page_height - 2.15 * inch, "This certificate is proudly presented to")

    pdf.setFont("Times-Bold", 32)
    pdf.setFillColor(colors.HexColor("#0F766E"))
    pdf.drawCentredString(page_width / 2, page_height - 2.9 * inch, recipient_name)

    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(page_width / 2, page_height - 3.45 * inch, "for successfully completing")

    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(page_width / 2, page_height - 3.95 * inch, course_name)

    if event_name:
        pdf.setFont("Helvetica", 12)
        pdf.drawCentredString(page_width / 2, page_height - 4.35 * inch, f"as part of {event_name}")

    if custom_message:
        pdf.setFont("Helvetica-Oblique", 11)
        pdf.drawCentredString(page_width / 2, page_height - 4.8 * inch, custom_message[:120])

    pdf.setFont("Helvetica", 11)
    pdf.drawString(1.25 * inch, 1.25 * inch, f"Issue date: {issue_date}")
    pdf.drawRightString(page_width - 1.25 * inch, 1.25 * inch, f"Issued by: {issuer_name}")

    pdf.save()
    return output_path
