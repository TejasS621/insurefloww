"""Policy document generation helpers for the provider backend."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from backend.provider_backend.core.models.policy_model import Policy


class PolicyDocumentService:
    """Generate simple PDF documents for issued policies."""

    def generate_policy_pdf(self, policy: Policy) -> Path:
        """Generate a PDF document for an issued policy and return its absolute path."""
        output_dir = Path("storage") / "policies"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{policy.policy_number}.pdf"

        pdf = canvas.Canvas(str(output_path), pagesize=A4)
        width, height = A4

        pdf.setTitle(f"Policy {policy.policy_number}")
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(50, height - 70, "InsureFlow Policy Document")

        pdf.setFont("Helvetica", 11)
        lines = [
            f"Policy Number: {policy.policy_number}",
            f"Policy Status: {policy.policy_status.value}",
            f"Main Transaction Reference: {policy.main_transaction_reference}",
            f"Provider Transaction Reference: {policy.provider_transaction_reference}",
            f"Payment Reference: {policy.payment_reference}",
            f"Provider Quote Reference: {policy.provider_quote_id}",
            f"Coverage Amount: INR {policy.coverage_amount:,.2f}",
            f"Premium Amount: INR {policy.premium_amount:,.2f}",
            f"Issue Date: {policy.issue_date.isoformat() if policy.issue_date else 'N/A'}",
            f"Start Date: {policy.start_date.isoformat() if policy.start_date else 'N/A'}",
            f"End Date: {policy.end_date.isoformat() if policy.end_date else 'N/A'}",
        ]

        vertical_position = height - 120
        for line in lines:
            pdf.drawString(50, vertical_position, line)
            vertical_position -= 24

        pdf.setFont("Helvetica-Oblique", 10)
        pdf.drawString(
            50,
            vertical_position - 20,
            "This is a system-generated policy document for development and testing purposes.",
        )
        pdf.showPage()
        pdf.save()
        return output_path.resolve()


policy_document_service = PolicyDocumentService()
