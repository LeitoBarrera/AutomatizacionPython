from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image
import os

def crear_pdf(cedula, folder):
    pdf_path = f'{folder}/{cedula}_antecedentes.pdf'
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, f"Reporte de antecedentes - Documento: {cedula}")

    y_position = height - 100
    for img_file in sorted(os.listdir(folder)):
        if img_file.endswith('.png'):
            img_path = os.path.join(folder, img_file)
            img = Image.open(img_path)
            img.thumbnail((500, 500))
            img.save(img_path)
            c.drawImage(img_path, 50, y_position - 300, width=500, height=300)
            y_position -= 350
            if y_position < 100:
                c.showPage()
                c.setFont("Helvetica-Bold", 14)
                y_position = height - 100

    c.save()
    return pdf_path