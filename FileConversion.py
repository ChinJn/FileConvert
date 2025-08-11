# webp or avif file

import streamlit as st
from PIL import Image, ImageFile
import io
import zipfile

# Allow truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

st.title("📷 Image Converter to WebP or AVIF")

# Session state for uploads
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = None

# Fixed settings
QUALITY_STEP = 5
MIN_QUALITY = 10  # fixed min quality

# Sidebar: adjustable settings
st.sidebar.header("⚙️ Conversion Settings")
max_width = st.sidebar.number_input("Max Width (px)", value=1920, step=100)
max_height = st.sidebar.number_input("Max Height (px)", value=1920, step=100)
initial_quality = st.sidebar.number_input("Initial Quality", value=80, min_value=1, max_value=100, step=1)

# Target size in MB (convert to bytes internally)
target_size_mb = st.sidebar.number_input("Target Size (MB)", value=1.0, step=0.1, format="%.2f")
target_size = int(target_size_mb * 1024 * 1024)

output_format = st.sidebar.selectbox("Output Format", ["WEBP", "AVIF"])  # new format selection


# Upload & Refresh buttons
col1, col2 = st.columns([4, 1])
with col1:
    uploaded_files = st.file_uploader(
        "Upload your images",
        type=["jpg", "jpeg", "png", "tif", "tiff"],
        accept_multiple_files=True
    )
with col2:
    if st.button("🔄 Refresh"):
        st.session_state["uploaded_files"] = None
        st.rerun()

# Store uploaded files in session
if uploaded_files:
    st.session_state.uploaded_files = uploaded_files

# Resize helper
def resize_image(img, max_w, max_h):
    width, height = img.size
    aspect_ratio = width / height
    if width > max_w or height > max_h:
        if aspect_ratio > 1:
            new_width = max_w
            new_height = int(max_w / aspect_ratio)
        else:
            new_height = max_h
            new_width = int(max_h * aspect_ratio)
        return img.resize((new_width, new_height), Image.LANCZOS)
    return img

# Convert button
if st.session_state.uploaded_files:
    if st.button("🚀 Convert"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for file in st.session_state.uploaded_files:
                try:
                    img = Image.open(file).convert("RGB")
                    img = resize_image(img, max_width, max_height)

                    temp_quality = initial_quality
                    img_bytes = io.BytesIO()

                    while temp_quality >= MIN_QUALITY:
                        img_bytes.seek(0)
                        img.save(img_bytes, output_format.lower(), quality=temp_quality)
                        size = img_bytes.tell()
                        if size <= target_size:
                            break
                        temp_quality -= QUALITY_STEP

                    img_bytes.seek(0)
                    output_filename = file.name.rsplit(".", 1)[0] + f".{output_format.lower()}"
                    zip_file.writestr(output_filename, img_bytes.read())

                except Exception as e:
                    st.error(f"❌ Error processing {file.name}: {e}")

        zip_buffer.seek(0)
        st.download_button(
            label=f"📥 Download All Converted Images as {output_format} (ZIP)",
            data=zip_buffer,
            file_name=f"converted_images_{output_format.lower()}.zip",
            mime="application/zip"
        )
