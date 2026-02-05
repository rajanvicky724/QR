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

# Sidebar for QR customization
st.sidebar.header("⚙️ Position & Size")

# --- NEW: Alignment Selector ---
h_anchor = st.sidebar.radio(
    "Horizontal Reference Point:",
    ["From Right Edge", "From Left Edge"],
    help="Choose 'Right' to keep it near the margin, or 'Left' for a fixed X coordinate."
)

if h_anchor == "From Right Edge":
    x_input = st.sidebar.number_input(
        "Distance from Right Edge (px)", 
        min_value=0, max_value=600, value=40, step=5,
        help="Increase this to move LEFT. Decrease to move RIGHT."
    )
else:
    x_input = st.sidebar.number_input(
        "Distance from Left Edge (px)", 
        min_value=0, max_value=600, value=450, step=5,
        help="Increase this to move RIGHT. Decrease to move LEFT."
    )

y_position = st.sidebar.number_input(
    "Y Position from Bottom (px)", 
    min_value=0, max_value=800, value=83, step=5
)

qr_size = st.sidebar.number_input(
    "QR Code Size (px)", 
    min_value=30, max_value=200, value=70, step=5
)

st.sidebar.markdown("---")
st.sidebar.header("📝 Text Settings")
show_text = st.sidebar.checkbox("Show enrollment text", value=True)
custom_text = st.sidebar.text_input("Text below QR", value="Scan your custom QR code to enroll")
text_font_size = st.sidebar.number_input("Font Size", value=7)

# Main content area
col1, col2 = st.columns(2)
with col1:
    uploaded_pdf = st.file_uploader("1. Upload PDF File", type=["pdf"])
with col2:
    uploaded_csv = st.file_uploader("2. Upload CSV File (with 'URL' column)", type=["csv"])

# Process button
if uploaded_pdf and uploaded_csv:
    if st.button("🚀 Generate PDF", type="primary"):
        with st.spinner("Processing..."):
            try:
                temp_dir = tempfile.mkdtemp()
                qr_folder = os.path.join(temp_dir, "qr_temp")
                os.makedirs(qr_folder, exist_ok=True)
                
                df = pd.read_csv(uploaded_csv)
                if "URL" not in df.columns:
                    st.error("❌ CSV must contain a 'URL' column!")
                    st.stop()
                
                reader = PdfReader(uploaded_pdf)
                writer = PdfWriter()
                total_pages = len(reader.pages)
                
                progress_bar = st.progress(0)
                
                for i in range(total_pages):
                    if i >= len(df): break # Stop if no more URLs
                    
                    url = df.iloc[i]["URL"]
                    
                    # Generate QR
                    qr = qrcode.make(url)
                    qr_path = os.path.join(qr_folder, f"qr_{i}.png")
                    qr.save(qr_path)
                    
                    # Create Overlay
                    overlay_pdf = os.path.join(qr_folder, f"overlay_{i}.pdf")
                    c = canvas.Canvas(overlay_pdf, pagesize=letter)
                    
                    # --- CALCULATE X/Y POSITION ---
                    page_width = float(reader.pages[i].mediabox.width)
                    
                    if h_anchor == "From Right Edge":
                        # Move Left = Increase x_input
                        # Move Right = Decrease x_input
                        x = page_width - qr_size - x_input
                    else:
                        # Move Left = Decrease x_input
                        # Move Right = Increase x_input
                        x = x_input

                    y = y_position
                    
                    # Draw
                    c.drawImage(qr_path, x, y, width=qr_size, height=qr_size)
                    
                    if show_text and custom_text:
                        c.setFont("Helvetica", text_font_size)
                        c.drawCentredString(x + qr_size / 2, y - 10, custom_text)
                    
                    c.save()
                    
                    # Merge
                    base_page = reader.pages[i]
                    overlay_page = PdfReader(overlay_pdf).pages[0]
                    base_page.merge_page(overlay_page)
                    writer.add_page(base_page)
                    
                    progress_bar.progress((i + 1) / total_pages)
                
                # Save & Download
                output_buffer = BytesIO()
                writer.write(output_buffer)
                output_buffer.seek(0)
                shutil.rmtree(temp_dir)
                
                st.success("✅ Done!")
                st.download_button(
                    "⬇️ Download Final PDF",
                    data=output_buffer,
                    file_name="output_qr.pdf",
                    mime="application/pdf",
                    type="primary"
                )
                
            except Exception as e:
                st.error(f"Error: {e}")

