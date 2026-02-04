import streamlit as st
import pandas as pd
import qrcode
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
import tempfile
import shutil
from io import BytesIO

st.set_page_config(page_title="QR Code PDF Generator", page_icon="📄", layout="wide")

st.title("📄 QR Code PDF Generator")
st.markdown("Upload a PDF and CSV file to add custom QR codes to each page")

# Sidebar for QR customization
st.sidebar.header("⚙️ QR Code Settings")

# Input fields for coordinates and size
x_offset = st.sidebar.number_input(
    "X Offset from Right Edge (px)", 
    min_value=0, 
    max_value=500, 
    value=40, 
    step=5,
    help="Distance from the right edge of the page"
)

y_position = st.sidebar.number_input(
    "Y Position from Bottom (px)", 
    min_value=0, 
    max_value=800, 
    value=83, 
    step=5,
    help="Distance from the bottom of the page"
)

qr_size = st.sidebar.number_input(
    "QR Code Size (px)", 
    min_value=30, 
    max_value=200, 
    value=70, 
    step=5,
    help="Width and height of the QR code"
)

show_text = st.sidebar.checkbox("Show enrollment text below QR", value=True)

custom_text = st.sidebar.text_input(
    "Custom Text (optional)",
    value="Scan your custom QR code to enroll",
    help="Text to display below QR code"
)

text_font_size = st.sidebar.number_input(
    "Text Font Size", 
    min_value=4, 
    max_value=14, 
    value=7, 
    step=1
)

# Main content area
col1, col2 = st.columns(2)

with col1:
    st.subheader("📤 Upload Files")
    uploaded_pdf = st.file_uploader("Upload PDF File", type=["pdf"])
    
with col2:
    uploaded_csv = st.file_uploader("Upload CSV File (with 'URL' column)", type=["csv"])

# Preview settings
if st.sidebar.button("🔍 Preview Settings"):
    st.sidebar.info(f"""
    **Current Settings:**
    - X Position: {x_offset}px from right
    - Y Position: {y_position}px from bottom
    - QR Size: {qr_size}x{qr_size}px
    - Text: {'Enabled' if show_text else 'Disabled'}
    """)

# Process button
if uploaded_pdf and uploaded_csv:
    if st.button("🚀 Generate PDF with QR Codes", type="primary"):
        
        with st.spinner("Processing... Please wait"):
            try:
                # Create temporary directory
                temp_dir = tempfile.mkdtemp()
                qr_folder = os.path.join(temp_dir, "qr_temp")
                os.makedirs(qr_folder, exist_ok=True)
                
                # Read CSV
                df = pd.read_csv(uploaded_csv)
                
                # Validate CSV has URL column
                if "URL" not in df.columns:
                    st.error("❌ CSV must contain a 'URL' column!")
                    shutil.rmtree(temp_dir)
                    st.stop()
                
                # Read PDF
                reader = PdfReader(uploaded_pdf)
                writer = PdfWriter()
                
                total_pages = len(reader.pages)
                
                # Show warning if counts don't match
                if len(df) != total_pages:
                    st.warning(f"⚠️ Warning: CSV has {len(df)} rows but PDF has {total_pages} pages!")
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i in range(total_pages):
                    # Check if URL exists for this page
                    if i >= len(df):
                        st.warning(f"⚠️ No URL for page {i+1}, skipping QR code")
                        writer.add_page(reader.pages[i])
                        continue
                    
                    url = df.iloc[i]["URL"]
                    
                    # Update status
                    status_text.text(f"Processing page {i + 1} of {total_pages}...")
                    
                    # Create QR code
                    qr = qrcode.make(url)
                    qr_path = os.path.join(qr_folder, f"qr_{i}.png")
                    qr.save(qr_path)
                    
                    # Create overlay PDF
                    overlay_pdf = os.path.join(qr_folder, f"overlay_{i}.pdf")
                    c = canvas.Canvas(overlay_pdf, pagesize=letter)
                    
                    # Calculate position
                    page_width = float(reader.pages[i].mediabox.width)
                    x = page_width - qr_size - x_offset
                    y = y_position
                    
                    # Draw QR code
                    c.drawImage(qr_path, x, y, width=qr_size, height=qr_size)
                    
                    # Draw text if enabled
                    if show_text and custom_text:
                        c.setFont("Helvetica", text_font_size)
                        c.drawCentredString(x + qr_size / 2, y - 10, custom_text)
                    
                    c.save()
                    
                    # Merge with original page
                    base_page = reader.pages[i]
                    overlay_page = PdfReader(overlay_pdf).pages[0]
                    base_page.merge_page(overlay_page)
                    
                    writer.add_page(base_page)
                    
                    # Update progress
                    progress_bar.progress((i + 1) / total_pages)
                
                # Save to BytesIO
                output_buffer = BytesIO()
                writer.write(output_buffer)
                output_buffer.seek(0)
                
                # Clean up temp files
                shutil.rmtree(temp_dir)
                
                status_text.text("✅ Processing complete!")
                progress_bar.progress(100)
                
                st.success(f"🎉 Successfully added QR codes to {total_pages} pages!")
                
                # Download button
                st.download_button(
                    label="⬇️ Download PDF with QR Codes",
                    data=output_buffer,
                    file_name="output_with_qr_codes.pdf",
                    mime="application/pdf",
                    type="primary"
                )
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                # Clean up on error
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

else:
    st.info("👆 Please upload both PDF and CSV files to get started")
    
    # Show example CSV format
    with st.expander("📋 CSV Format Example"):
        st.markdown("""
        Your CSV file should have a column named **URL** with one URL per row:
        
        ```
        URL
        https://example.com/page1
        https://example.com/page2
        https://example.com/page3
        ```
        
        Each row corresponds to one page in the PDF.
        """)

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit | Upload files to add QR codes to your PDFs")
