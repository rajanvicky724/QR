import streamlit as st
import streamlit.components.v1 as components  # Required for Google Verification
import pandas as pd
import qrcode
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
import tempfile
import shutil
from io import BytesIO
from streamlit_extras.buy_me_a_coffee import button

# --- 1. GOOGLE VERIFICATION (Must be at the top) ---
components.html(
    """
    <head>
        <meta name="google-site-verification" content="QkVR09fdIHwZy3gbNlK8-0pNxanAZyOQUXqSdX7ARB8" />
    </head>
    """,
    height=0,
)

# --- 2. SEO & PAGE CONFIG ---
st.set_page_config(
    page_title="Free Bulk QR Code Generator from URL | CSV to PDF Tool", 
    page_icon="📄", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.buymeacoffee.com/vigneshna',
        'About': "Free tool to generate bulk QR codes from CSV and overlay them on PDFs."
    }
)

# --- 3. HIDDEN SEO TEXT ---
st.markdown(
    """
    <div style="display:none;">
    <h1>Free Bulk QR Code Generator Online</h1>
    <p>Generate thousands of QR codes from CSV URLs instantly. 
    Best free tool to convert Excel/CSV links to printable PDF QR codes. 
    Features: Bulk generation, PDF overlay, position customization, and high-quality download.</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.title("📄 QR Code PDF Generator")
st.caption("🚀 The easiest way to create bulk QR codes from a CSV list and place them onto your PDF files.")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("⚙️ Position & Size")

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

# --- MAIN UPLOAD AREA ---
col1, col2 = st.columns(2)
with col1:
    uploaded_pdf = st.file_uploader("1. Upload PDF File", type=["pdf"])
with col2:
    uploaded_csv = st.file_uploader("2. Upload CSV File (with 'URL' column)", type=["csv"])

# --- PROCESS BUTTON ---
if uploaded_pdf and uploaded_csv:
    if st.button("🚀 Generate PDF", type="primary"):
        with st.spinner("Processing..."):
            try:
                temp_dir = tempfile.mkdtemp()
                qr_folder = os.path.join(temp_dir, "qr_temp")
                os.makedirs(qr_folder, exist_ok=True)
                
                df = pd.read_csv(uploaded_csv)
                # Check for URL column (case insensitive fix optional, but sticking to strict for now)
                if "URL" not in df.columns:
                    st.error("❌ CSV must contain a column named 'URL'!")
                    st.stop()
                
                reader = PdfReader(uploaded_pdf)
                writer = PdfWriter()
                total_pages = len(reader.pages)
                
                progress_bar = st.progress(0)
                
                for i in range(total_pages):
                    if i >= len(df): break 
                    
                    url = df.iloc[i]["URL"]
                    
                    # Generate QR
                    qr = qrcode.make(url)
                    qr_path = os.path.join(qr_folder, f"qr_{i}.png")
                    qr.save(qr_path)
                    
                    # Create Overlay
                    overlay_pdf = os.path.join(qr_folder, f"overlay_{i}.pdf")
                    c = canvas.Canvas(overlay_pdf, pagesize=letter)
                    
                    # Position Logic
                    page_width = float(reader.pages[i].mediabox.width)
                    
                    if h_anchor == "From Right Edge":
                        x = page_width - qr_size - x_input
                    else:
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
                
                # Output
                output_buffer = BytesIO()
                writer.write(output_buffer)
                output_buffer.seek(0)
                shutil.rmtree(temp_dir)
                
                st.success("✅ PDF Generated Successfully!")
                
                st.download_button(
                    label="⬇️ Download Final PDF",
                    data=output_buffer,
                    file_name="output_qr.pdf",
                    mime="application/pdf",
                    type="primary"
                )
                
            except Exception as e:
                st.error(f"Error: {e}")

# --- CONTENT FOR USERS & SEO ---
st.markdown("---")
with st.expander("ℹ️ How to use this Bulk QR Generator", expanded=True):
    st.markdown("""
    ### 📌 How to create bulk QR codes for PDF?
    1. **Upload your PDF**: Select the document you want to modify (e.g., certificates, letters).
    2. **Upload CSV Data**: Create a CSV file with a header row named `URL` containing your links.
    3. **Customize Position**: Use the sidebar to move the QR code to the perfect spot.
    4. **Download**: Click "Generate" to get a single PDF with unique QR codes on every page.
    
    **✨ Key Features:**
    - **Bulk Processing**: Generate 100s of QR codes in seconds.
    - **Privacy First**: Files are processed in memory and not stored.
    - **Fully Customizable**: Adjust size, position, and text.
    """)

# --- FLOATING COFFEE BUTTON ---
button(username="vigneshna", floating=True, width=221)
