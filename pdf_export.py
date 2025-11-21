# pdf_export.py — Z9CoachLite

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from typing import Dict, Any


def generate_lite_report(profile_data: Dict[str, Any]) -> bytes:
    """
    Generate a 1-page PDF report for the Lite app.

    Expected keys in profile_data:
    - trait_score: float
    - harmony_ratio: float
    - stage: str
    - trait_summary: str (multi-line)
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 50, "Z9CoachLite — Daily Insight Report")

    # Main summary
    c.setFont("Helvetica", 12)
    y = height - 100

    trait_score = float(profile_data.get("trait_score", 0.0))
    harmony_ratio = float(profile_data.get("harmony_ratio", 0.0))
    stage = str(profile_data.get("stage", "N/A"))
    trait_summary = str(profile_data.get("trait_summary", "")).strip()

    c.drawString(50, y, f"Composite Trait Score: {trait_score:.2f}")
    y -= 20
    c.drawString(50, y, f"Harmony Ratio: {harmony_ratio:.1f}%")
    y -= 20
    c.drawString(50, y, f"Suggested Stage: {stage}")
    y -= 30

    # Trait summary (multi-line)
    c.drawString(50, y, "Trait Summary:")
    y -= 20
    text_object = c.beginText(50, y)
    text_object.setFont("Helvetica", 10)

    for line in trait_summary.splitlines():
        text_object.textLine(line)

    c.drawText(text_object)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
