from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def create_mock_exam_pdf(filename, course_name="Test Ders", num_questions=5):
    """
    Creates a mock exam PDF with questions and an answer key.
    """
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"{course_name} - Güz Dönemi Ara Sınavı")

    c.setFont("Helvetica", 12)
    y = height - 100

    answers = {}

    for i in range(1, num_questions + 1):
        if y < 150: # New page if low on space
            c.showPage()
            y = height - 50

        question_text = f"{i}. Aşağıdakilerden hangisi test sorusu {i}'nin cevabıdır?"
        c.drawString(50, y, question_text)
        y -= 20

        options = ["A", "B", "C", "D", "E"]
        correct_option = options[(i-1) % 5] # A, B, C, D, E, A...
        answers[i] = correct_option

        for opt in options:
            text = f"{opt}) Seçenek {opt} {'(Doğru)' if opt == correct_option else ''}"
            c.drawString(70, y, text)
            y -= 15

        y -= 20

    # Answer Key Page
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Cevap Anahtarı")

    c.setFont("Helvetica", 12)
    y = height - 80

    # Draw a simple table-like structure
    c.drawString(50, y, "Soru No   Cevap")
    y -= 20

    for i in range(1, num_questions + 1):
        c.drawString(50, y, f"{i}          {answers[i]}")
        y -= 15

    c.save()
    return answers

if __name__ == "__main__":
    create_mock_exam_pdf("test_exam.pdf")
    print("Created test_exam.pdf")
