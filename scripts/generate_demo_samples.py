"""
Generates curated demo samples for ClaimGuard:
- authentic_car.jpg & ai_car_damage.jpg
- clean_invoice.pdf & tampered_invoice.pdf
- id_card.jpg, matching_selfie.jpg, mismatch_selfie.jpg
"""
import io
import math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "demo_samples"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def make_clean_invoice(output_path: Path):
    doc = SimpleDocTemplate(str(output_path), pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("InvTitle", parent=styles["Heading1"], fontSize=18, leading=22, textColor=colors.HexColor("#0f172a"))
    meta_style = ParagraphStyle("InvMeta", parent=styles["Normal"], fontSize=9, leading=13, textColor=colors.HexColor("#475569"))
    bold_style = ParagraphStyle("InvBold", parent=styles["Normal"], fontSize=9, leading=13, fontName="Helvetica-Bold", textColor=colors.HexColor("#0f172a"))

    story = [
        Paragraph("<b>PREMIER COLLISION REPAIR CENTRE</b>", title_style),
        Paragraph("Authorized Insurance Estimate & Repair Invoice", meta_style),
        Spacer(1, 10),
        Paragraph("Invoice #: <b>INV-2026-8831</b> | Policy #: <b>POL-7729104</b>", bold_style),
        Paragraph("Claimant: <b>Arun Kumar</b> | Date: <b>2026-09-12</b> | Due Date: <b>2026-09-26</b>", meta_style),
        Spacer(1, 15),
    ]

    items = [
        ["Item #", "Repair / Replacement Description", "Qty", "Rate (INR)", "Amount (INR)"],
        ["1", "Front Bumper Fascia OEM Replacement", "1", "6,500.00", "6,500.00"],
        ["2", "Right Headlamp Assembly Matrix LED", "1", "12,000.00", "12,000.00"],
        ["3", "Fender Panel Alignment & Paint Labor", "1", "4,500.00", "4,500.00"],
        ["4", "Structural Sensor Recalibration", "1", "2,000.00", "2,000.00"],
        ["", "", "", "<b>Subtotal:</b>", "<b>25,000.00</b>"],
        ["", "", "", "<b>GST (18%):</b>", "<b>4,500.00</b>"],
        ["", "", "", "<b>Total Payable:</b>", "<b>29,500.00</b>"],
    ]

    table = Table(items, colWidths=[45, 260, 45, 90, 90])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (3, -1), (-1, -1), colors.HexColor("#f1f5f9")),
    ]))
    story.append(table)
    doc.build(story)
    print(f"Generated: {output_path}")


def make_tampered_invoice(output_path: Path):
    doc = SimpleDocTemplate(str(output_path), pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("InvTitle", parent=styles["Heading1"], fontSize=18, leading=22, textColor=colors.HexColor("#0f172a"))
    meta_style = ParagraphStyle("InvMeta", parent=styles["Normal"], fontSize=9, leading=13, textColor=colors.HexColor("#475569"))
    bold_style = ParagraphStyle("InvBold", parent=styles["Normal"], fontSize=9, leading=13, fontName="Helvetica-Bold", textColor=colors.HexColor("#0f172a"))

    story = [
        Paragraph("<b>PREMIER COLLISION REPAIR CENTRE</b>", title_style),
        Paragraph("Authorized Insurance Estimate & Repair Invoice", meta_style),
        Spacer(1, 10),
        Paragraph("Invoice #: <b>INV-2026-9942</b> | Policy #: <b>POL-7729104</b>", bold_style),
        Paragraph("Claimant: <b>Arun Kumar</b> | Date: <b>2026-09-12</b> | Due Date: <b>2026-09-01</b>", meta_style), # Chronology error: due before invoice
        Spacer(1, 15),
    ]

    # Tampered: Items sum to 25,000 + 4,500 = 29,500, but Total Payable was forged to 48,500.00!
    items = [
        ["Item #", "Repair / Replacement Description", "Qty", "Rate (INR)", "Amount (INR)"],
        ["1", "Front Bumper Fascia OEM Replacement", "1", "6,500.00", "6,500.00"],
        ["2", "Right Headlamp Assembly Matrix LED", "1", "12,000.00", "12,000.00"],
        ["3", "Fender Panel Alignment & Paint Labor", "1", "4,500.00", "4,500.00"],
        ["4", "Structural Sensor Recalibration", "1", "2,000.00", "2,000.00"],
        ["", "", "", "<b>Subtotal:</b>", "<b>25,000.00</b>"],
        ["", "", "", "<b>GST (18%):</b>", "<b>4,500.00</b>"],
        ["", "", "", "<b>Total Payable:</b>", "<b>48,500.00</b>"], # Mismatched total
    ]

    table = Table(items, colWidths=[45, 260, 45, 90, 90])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (3, -1), (-1, -1), colors.HexColor("#fee2e2")), # Highlighted row
    ]))
    story.append(table)
    doc.build(story)
    print(f"Generated: {output_path}")


def make_authentic_car_image(output_path: Path):
    w, h = 800, 600
    img = Image.new("RGB", (w, h), color=(140, 160, 180))
    draw = ImageDraw.Draw(img)

    # Road and background
    draw.rectangle([0, 380, w, h], fill=(60, 65, 70))
    draw.line([0, 480, w, 480], fill=(230, 230, 230), width=4)

    # Car body (clean camera photo look)
    draw.rounded_rectangle([150, 240, 650, 420], radius=40, fill=(30, 70, 140))
    draw.polygon([(240, 240), (320, 150), (520, 150), (580, 240)], fill=(20, 45, 80)) # Cabin
    draw.polygon([(255, 235), (325, 160), (515, 160), (565, 235)], fill=(180, 210, 230)) # Glass

    # Wheels
    draw.ellipse([220, 370, 310, 460], fill=(20, 20, 20))
    draw.ellipse([245, 395, 285, 435], fill=(160, 160, 160))
    draw.ellipse([490, 370, 580, 460], fill=(20, 20, 20))
    draw.ellipse([515, 395, 555, 435], fill=(160, 160, 160))

    # Add realistic sensor noise
    np_img = np.array(img).astype(np.float32)
    noise = np.random.normal(0, 3.5, np_img.shape)
    np_img = np.clip(np_img + noise, 0, 255).astype(np.uint8)

    clean_img = Image.fromarray(np_img)
    clean_img.save(output_path, "JPEG", quality=92)
    print(f"Generated: {output_path}")


def make_ai_damaged_car_image(output_path: Path):
    w, h = 800, 600
    img = Image.new("RGB", (w, h), color=(140, 160, 180))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 380, w, h], fill=(60, 65, 70))
    draw.line([0, 480, w, 480], fill=(230, 230, 230), width=4)

    draw.rounded_rectangle([150, 240, 650, 420], radius=40, fill=(180, 30, 30))
    draw.polygon([(240, 240), (320, 150), (520, 150), (580, 240)], fill=(40, 40, 40))
    draw.polygon([(255, 235), (325, 160), (515, 160), (565, 235)], fill=(180, 210, 230))

    draw.ellipse([220, 370, 310, 460], fill=(20, 20, 20))
    draw.ellipse([490, 370, 580, 460], fill=(20, 20, 20))

    # Splice / Inpaint a heavily altered crumpled dent on front bumper
    dent_box = [150, 300, 280, 420]
    draw.polygon([(150, 340), (220, 310), (270, 360), (230, 420), (160, 410)], fill=(70, 10, 10))
    draw.line([(160, 330), (210, 360), (260, 340)], fill=(10, 10, 10), width=3)
    draw.line([(180, 370), (230, 390)], fill=(20, 20, 20), width=2)

    # Convert to array and inject ELA compression discrepancy on the dent
    np_img = np.array(img).astype(np.float32)
    # Inject high frequency grid noise on dent
    y1, y2, x1, x2 = 300, 420, 150, 280
    np_img[y1:y2, x1:x2] += np.random.normal(15, 8.0, (y2 - y1, x2 - x1, 3))
    np_img = np.clip(np_img, 0, 255).astype(np.uint8)

    fake_img = Image.fromarray(np_img)
    fake_img.save(output_path, "JPEG", quality=75)
    print(f"Generated: {output_path}")


def make_faces(id_path: Path, selfie_path: Path, mismatch_path: Path):
    w, h = 300, 300

    def draw_face(skin_color, eye_color, hair_color, smile=True):
        img = Image.new("RGB", (w, h), color=(240, 240, 245))
        d = ImageDraw.Draw(img)
        # Hair
        d.ellipse([65, 40, 235, 180], fill=hair_color)
        # Face oval
        d.ellipse([80, 60, 220, 230], fill=skin_color)
        # Eyes
        d.ellipse([110, 115, 135, 135], fill=eye_color)
        d.ellipse([165, 115, 190, 135], fill=eye_color)
        # Nose
        d.polygon([(150, 130), (145, 165), (155, 165)], fill=(180, 130, 110))
        # Mouth
        if smile:
            d.arc([125, 165, 175, 195], 0, 180, fill=(160, 40, 40), width=3)
        else:
            d.line([130, 180, 170, 180], fill=(160, 40, 40), width=3)
        return img

    f1 = draw_face((235, 185, 155), (40, 60, 80), (30, 20, 15), smile=False)
    f1.save(id_path, "JPEG", quality=90)

    f1_selfie = draw_face((235, 185, 155), (40, 60, 80), (30, 20, 15), smile=True)
    f1_selfie.save(selfie_path, "JPEG", quality=90)

    f2 = draw_face((210, 160, 130), (80, 50, 20), (200, 160, 50), smile=True)
    f2.save(mismatch_path, "JPEG", quality=90)


if __name__ == "__main__":
    make_clean_invoice(OUTPUT_DIR / "clean_invoice.pdf")
    make_tampered_invoice(OUTPUT_DIR / "tampered_invoice.pdf")
    make_authentic_car_image(OUTPUT_DIR / "authentic_car.jpg")
    make_ai_damaged_car_image(OUTPUT_DIR / "ai_car_damage.jpg")
    make_faces(
        OUTPUT_DIR / "id_card.jpg",
        OUTPUT_DIR / "matching_selfie.jpg",
        OUTPUT_DIR / "mismatch_selfie.jpg",
    )
    print("All curated demo samples generated successfully in data/demo_samples!")
