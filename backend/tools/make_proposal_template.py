"""Build templates/proposal_template.docx: the proposal template that code fills."""
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

OUT = Path(__file__).resolve().parent.parent / "templates" / "proposal_template.docx"
NAVY = RGBColor(0x1F, 0x2A, 0x44)


def heading(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text.upper())
    run.bold, run.font.size, run.font.color.rgb = True, Pt(11), NAVY
    p.paragraph_format.space_before = Pt(14)
    return p


doc = Document()
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(10.5)

title = doc.add_paragraph()
run = title.add_run("{{PROPERTY_NAME}}")
run.bold, run.font.size, run.font.color.rgb = True, Pt(20), NAVY
doc.add_paragraph("{{PROPERTY_ADDRESS}}")

heading(doc, "Group accommodation proposal")
doc.add_paragraph("Reference: {{PROPOSAL_REF}}    Date: {{PROPOSAL_DATE}}")

heading(doc, "Prepared for")
doc.add_paragraph("{{CLIENT_NAME}}\n{{CLIENT_COMPANY}}\n{{CLIENT_EMAIL}}")

heading(doc, "Your event")
doc.add_paragraph("Event: {{EVENT_NAME}}\nArrival: {{ARRIVAL_DATE}}    Departure: {{DEPARTURE_DATE}}\nNights: {{NIGHT_COUNT}}")

heading(doc, "Room rates")
doc.add_paragraph("Rates are per room per night in {{CURRENCY}}. {{TAX_NOTE}}")
table = doc.add_table(rows=2, cols=5)
table.style = "Light Grid Accent 1"
for cell, label in zip(table.rows[0].cells, ["Date", "Room type", "Rooms", "Rate per night", "Amount"]):
    cell.text = label
    cell.paragraphs[0].runs[0].bold = True
for cell, label in zip(table.rows[1].cells, ["{{ROW_DATE}}", "{{ROW_ROOM_TYPE}}", "{{ROW_ROOMS}}", "{{ROW_RATE}}", "{{ROW_AMOUNT}}"]):
    cell.text = label
for row in table.rows:
    for cell in row.cells[2:]:
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

total = doc.add_paragraph()
total.paragraph_format.space_before = Pt(8)
total.add_run("Total room nights: {{TOTAL_ROOM_NIGHTS}}    Total room revenue: {{CURRENCY}} {{TOTAL_REVENUE}}").bold = True

heading(doc, "Additional services")
doc.add_paragraph("{{ADDITIONAL_SERVICES}}")

heading(doc, "Terms and conditions")
doc.add_paragraph("Option date: {{OPTION_DATE}}\nAttrition: {{ATTRITION}}\nCancellation: {{CANCELLATION}}")

heading(doc, "Contact")
doc.add_paragraph("{{SALESPERSON_NAME}}, {{SALESPERSON_TITLE}}\n{{SALESPERSON_EMAIL}}")

OUT.parent.mkdir(exist_ok=True)
doc.save(OUT)
print("wrote", OUT)
