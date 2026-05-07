import markdown
import pdfkit

def export_markdown_to_pdf(md_content: str, output_path: str):
    """
    Converts markdown content to an HTML string, and then exports it to a PDF file.
    Note: pdfkit requires wkhtmltopdf to be installed on the system.
    """
    try:
        html_content = markdown.markdown(md_content)
        # Add basic styling for better UI presentation in the PDF
        styled_html = f\"\"\"
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; color: #333; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
                h3 {{ color: #7f8c8d; }}
                a {{ color: #3498db; text-decoration: none; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        \"\"\"
        pdfkit.from_string(styled_html, output_path)
    except Exception as e:
        print(f"Failed to export to PDF. Make sure wkhtmltopdf is installed on your system. Error: {e}")
