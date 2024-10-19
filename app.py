from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
import io

app = Flask(__name__)

def wrap_text(text, canvas, max_width):
    """
    Splits text into multiple lines to fit within the specified width.
    Handles newline characters (\n) to ensure proper line breaks.
    """
    lines = []
    paragraphs = text.split('\n')

    for paragraph in paragraphs:
        words = paragraph.split(' ')
        current_line = []

        for word in words:
            current_line.append(word)
            # Check if the current line width exceeds max_width
            if canvas.stringWidth(' '.join(current_line)) > max_width:
                lines.append(' '.join(current_line[:-1]))  # Add current line without last word
                current_line = [word]  # Start new line with the word that was too long

        # Add any remaining words as the last line
        if current_line:
            lines.append(' '.join(current_line))

        # Add an empty line to represent the newline character between paragraphs
        lines.append('')

    return lines

def draw_text(p, text, x, y, max_width=500, font_size=12):
    """
    Draws text with consistent font size, managing line breaks and text wrapping.
    """
    p.setFont("Times-Roman", font_size)  # Ensure consistent font size
    lines = wrap_text(text, p, max_width)
    for line in lines:
        if y < 1 * inch:  # Check if space is low on the page
            p.showPage()  # Start a new page
            y = 10 * inch  # Reset y to the top margin for the new page
            p.setFont("Times-Roman", font_size)
        p.drawString(x, y, line)
        y -= font_size + 2  # Adjust for consistent line spacing
    return y



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            details = {
                'name': request.form['name'],
                'email': request.form['email'],
                'contact': request.form['contact'],
                'role': request.form['role'],
                'profile': request.form['profile'].replace('\r\n', '\n').replace('\r', '\n'),
                'education': request.form['education'].replace('\r\n', '\n').replace('\r', '\n'),
                'training_and_certificates': request.form['training_and_certificates'].replace('\r\n', '\n').replace('\r', '\n'),
                'experience': request.form['experience'].replace('\r\n', '\n').replace('\r', '\n'),
                'skills': request.form['skills'].replace('\r\n', '\n').split(','),  # Keep it as a list
                'projects': request.form['projects'].replace('\r\n', '\n').replace('\r', '\n')
            }

            # Set up PDF buffer and canvas
            pdf_buffer = io.BytesIO()
            p = canvas.Canvas(pdf_buffer, pagesize=A4)
            width, height = A4

            y_pos = height - 72  # Start position from the top of the page
            left_margin = 72  # Left margin for content
            max_width = width - 2 * left_margin


            # Function to draw each section with wrapped text
            def draw_section(title, content, y):
                if content.strip():  # Check if content is not empty
                    p.setFont("Times-Bold", 12)
                    p.drawString(left_margin, y, title)
                    y -= 16

                    p.setFont("Times-Roman", 10)
                    wrapped_lines = wrap_text(content, p,  max_width)
                    for line in wrapped_lines:
                        if y < 72:  # If running out of space, create a new page
                            p.showPage()
                             # Resetting font and y position on new page
                            p.setFont("Times-Roman", 10)  # Resetting font for new page
                            y = height - 72
                            #p.drawString(left_margin, y, title)  # Re-draw title if necessary
                            #y -= 16  # Space for title

                            
                        p.drawString(left_margin, y, line)
                        y -= 14
                    y -= 8  # Add some space after each section
                   
                return y

            # Draw content on the PDF
            p.setFont("Times-Bold", 18)
            p.drawString(left_margin, y_pos, details['name'])
            y_pos -= 20

            p.setFont("Times-Roman", 12)
            p.drawString(left_margin, y_pos, f"Email: {details['email']} | Contact: {details['contact']}")
            y_pos -= 20

            p.setFont("Times-Bold", 14)
            p.drawString(left_margin, y_pos, details['role'])
            y_pos -= 24

            y_pos = draw_section("Profile Summary", details['profile'], y_pos)
            y_pos = draw_section("Education", details['education'], y_pos)
            #y_pos = draw_section("Training & Certificates", details['training_and_certificates'], y_pos)
            #y_pos = draw_section("Work Experience", details['experience'], y_pos)
           #Only draw these sections if they have content
            if details['training_and_certificates'].strip():  # Check for training and certificates
                y_pos = draw_section("Training & Certificates", details['training_and_certificates'], y_pos)

            if details['experience'].strip():  # Check for work experience
                y_pos = draw_section("Work Experience", details['experience'], y_pos)
            y_pos = draw_section("Skills", ', '.join([skill.strip() for skill in details['skills'] if skill]), y_pos)
            y_pos = draw_section("Projects", details['projects'], y_pos)

            # Finalize and save the PDF
            p.showPage()
            p.save()

            pdf_buffer.seek(0)
            return send_file(pdf_buffer, as_attachment=True, download_name='resume.pdf', mimetype='application/pdf')

        except Exception as e:
            return f"An error occurred: {e}", 500

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
