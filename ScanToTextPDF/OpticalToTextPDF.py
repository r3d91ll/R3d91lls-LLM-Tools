from pdf2image import convert_from_path
import pytesseract
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

def convert_pdf_to_text(pdf_path, output_path):
    # Convert PDF to a list of images
    images = convert_from_path(pdf_path)

    # Create a PDF for output
    c = canvas.Canvas(output_path, pagesize=letter)

    for image in images:
        # Perform OCR on the image
        text = pytesseract.image_to_string(image)

        # Move the cursor to the top of the page for each new image
        c.drawString(30, 750, text)
        c.showPage()

    c.save()

# Path to your scanned PDF
pdf_path = "/home/todd6585/Downloads/Symbols_of_Political_Competition_and_Leadership.pdf"

# Path for the new text-based PDF
output_path = "/home/todd6585/git/R3d91ll-repos/R3d91lls-LLM-Tools/ScanToTextPDF/Symbols_of_Political_Competition_and_Leadership.pdf"

# Convert the PDF
convert_pdf_to_text(pdf_path, output_path)
