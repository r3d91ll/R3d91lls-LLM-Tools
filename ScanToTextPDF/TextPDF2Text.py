from PyPDF2 import PdfReader
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Function to read a PDF and convert it to a text-based PDF
def convert_scanned_pdf_to_text(pdf_path, output_path):
    # Convert PDF to a list of images
    images = convert_from_path(pdf_path)

    # Create a PDF for the output
    c = canvas.Canvas(output_path, pagesize=letter)

    for image in images:
        # Perform OCR on the image
        text = pytesseract.image_to_string(image)

        # Split text into lines
        lines = text.split('\n')
        x_margin, y_position = 30, 750

        # Write each line to the PDF
        for line in lines:
            if y_position < 50:  # Add new page if there's no space left
                c.showPage()
                y_position = 750
            c.drawString(x_margin, y_position, line)
            y_position -= 12  # Move to the next line

        c.showPage()

    c.save()

# Path to the user's scanned PDF
pdf_path = '/home/todd6585/Downloads/Symbols_of_Political_Competition_and_Leadership.pdf'

# Path for the new text-based PDF
output_path = '/home/todd6585/git/R3d91ll-repos/R3d91lls-LLM-Tools/ScanToTextPDF/Symbols_of_Political_Competition_and_Leadership.pdf'

# Convert the PDF
convert_scanned_pdf_to_text(pdf_path, output_path)

output_path

