"""Generate sample binary PDF and DOCX files for offline testing and demonstration."""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import docx


def generate_pdf(output_path: Path):
    """Generate a realistic sample PDF with pages and headers."""
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter

    # Page 1
    c.setFont("Helvetica-Bold", 16)
    c.drawString(54, height - 54, "Site Reliability Engineering Incident Response SOP")
    c.setFont("Helvetica", 10)
    c.drawString(54, height - 74, "Document Version 2.4 | Classification: Enterprise Confidential")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(54, height - 110, "1. Incident Severity Definitions")
    c.setFont("Helvetica", 10)
    text = c.beginText(54, height - 130)
    text.textLine("Severity-1 (Critical Outage): Core user-facing functionality is fully unavailable.")
    text.textLine("The escalation bridge must be convened within 5 minutes.")
    text.textLine("Executive leadership notification is required within 15 minutes.")
    text.textLine("Status page public updates must occur every 20 minutes until resolved.")
    text.textLine("")
    text.textLine("Severity-2 (Major Impairment): Critical feature degraded with significant impact.")
    text.textLine("The escalation bridge must be convened within 15 minutes.")
    text.textLine("Status updates are provided every 45 minutes.")
    c.drawText(text)

    c.showPage()

    # Page 2
    c.setFont("Helvetica-Bold", 12)
    c.drawString(54, height - 54, "2. Command Authority and Roles")
    c.setFont("Helvetica", 10)
    text2 = c.beginText(54, height - 74)
    text2.textLine("The Incident Commander (IC) or Lead SRE has single-point operational authority")
    text2.textLine("to declare a Severity-1 incident, order service rollbacks, and direct response teams.")
    text2.textLine("")
    text2.textLine("A blameless root-cause analysis (RCA) must be published within 72 hours of closure,")
    text2.textLine("including a chronological timeline, contributing causes, and preventive action items.")
    c.drawText(text2)

    c.save()
    print(f"Generated PDF at {output_path}")


def generate_docx(output_path: Path):
    """Generate a realistic sample DOCX with styles, headings, and paragraphs."""
    doc = docx.Document()
    doc.core_properties.title = "Corporate Responsible AI and Data Governance Policy"
    doc.core_properties.author = "KnowledgeForge Security & Compliance Office"

    doc.add_heading("Corporate Responsible AI, LLM Security & Data Governance Policy", level=0)

    doc.add_heading("1. Purpose and Scope", level=1)
    doc.add_paragraph(
        "This policy governs the ethical deployment, data boundary protection, security compliance, "
        "and safe usage of Generative AI, Retrieval-Augmented Generation (RAG), and Large Language Models (LLMs)."
    )

    doc.add_heading("2. Customer Data Privacy and Foundation Model Training", level=1)
    doc.add_paragraph(
        "Customer data, uploaded corporate documents, proprietary source code, and employee prompts "
        "are strictly prohibited from being used to train, retrain, or fine-tune public foundation models "
        "or third-party commercial LLMs without explicit contractual consent."
    )
    doc.add_paragraph(
        "AES-256 encryption is required for all persistent storage volumes, and TLS 1.3 is required for data in transit."
    )

    doc.add_heading("3. Grounding and Anti-Hallucination Controls", level=1)
    doc.add_paragraph(
        "All enterprise automated decision-support assistants must implement grounded RAG pipelines. "
        "Language models must state when sufficient supporting evidence is absent from retrieved knowledge chunks "
        "rather than speculating or fabricating responses."
    )

    doc.save(str(output_path))
    print(f"Generated DOCX at {output_path}")


if __name__ == "__main__":
    out_dir = Path(__file__).parent
    generate_pdf(out_dir / "incident_response_sop.pdf")
    generate_docx(out_dir / "ai_governance_policy.docx")

