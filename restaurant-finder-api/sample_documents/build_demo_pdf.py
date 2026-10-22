"""Reproducibly build the two synthetic text-based menu fixtures with ReportLab.

Developer utility only; ReportLab is not an application dependency.
"""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor


def build(path: Path, price: int, version: str):
    pdf = canvas.Canvas(str(path), pagesize=(595, 842), invariant=1)
    pdf.setTitle(f"Harbor Pasta Lab - fictional demo menu {version}")
    pdf.setFillColor(HexColor("#173e4b"))
    pdf.rect(0, 692, 595, 150, fill=1, stroke=0)
    pdf.setFillColor(HexColor("#ffffff"))
    pdf.setFont("Helvetica-Bold", 23)
    pdf.drawString(42, 778, "Harbor Pasta Lab")
    pdf.setFont("Helvetica", 13)
    pdf.drawString(42, 750, f"Fictional demo menu - {version}")
    pdf.setFillColor(HexColor("#263e48"))
    pdf.setFont("Helvetica", 11)
    pdf.drawString(42, 655, "Synthetic engineering fixture. This document describes no real venue.")
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(42, 610, "Main dishes")
    pdf.setFont("Helvetica", 11)
    for y, text in [(578, f"Mushroom pasta - RM{price} per serving. Contains wheat and milk."),
                    (550, "Tomato pasta - RM24 per serving. Vegan. Available at lunch and dinner."),
                    (522, "Garlic bread - RM9 per plate. Contains wheat and milk.")]:
        pdf.drawString(42, y, text)
    pdf.setStrokeColor(HexColor("#adc1c8"))
    pdf.line(42, 90, 553, 90)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(42, 66, f"Controlled corpus fixture | {version} | Page 1")
    pdf.save()


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    build(root / "harbor-menu.pdf", 28, "v1")
    build(root / "harbor-menu-v2.pdf", 32, "v2")
