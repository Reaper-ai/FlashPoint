import base64
import streamlit.components.v1 as components
from fpdf import FPDF
import io


# --- HELPER: PDF GENERATOR ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'FLASHPOINT INTELLIGENCE SITREP', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf(report_text, ):
    """Converts text report into a PDF byte stream"""
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    # Title
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Summary Report", 0, 1, 'L')
    pdf.ln(5)
    
    # Body
    pdf.set_font("Arial", size=11)
    # multi_cell handles line wrapping automatically
    # encode/decode handles some basic unicode issues compatible with FPDF
    safe_text = report_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, safe_text)
    
    # Return PDF as bytes
    return pdf.output(dest='S').encode('latin-1')


def trigger_auto_download(file_bytes, filename):
    """
    Injects Javascript to auto-download a file without user interaction.
    """
    b64 = base64.b64encode(file_bytes).decode()
    payload = f'data:application/pdf;base64,{b64}'
    
    html = f"""
    <html>
    <body>
        <a id="download_link" href="{payload}" download="{filename}" style="display:none;">Download</a>
        <script>
            document.getElementById('download_link').click();
        </script>
    </body>
    </html>
    """
    # Render invisible iframe that executes the JS
    components.html(html, height=0, width=0)