import streamlit as st
from PIL import Image, ImageFile
import io
import zipfile

# Allow truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

st.title("📷 Image to WebP Converter with Custom Size Limit")

# Settings
max_width = 1920
max_height = 1920
initial_quality = 80
min_quality = 10
quality_step = 5
allowed_extensions = ('.jpg', '.jpeg', '.png', '.tif', '.tiff')

# Preset sizes (KB)
size_presets = {
    "200 KB": 200 * 1024,
    "500 KB": 500 * 1024,
    "800 KB (default)": 800 * 1024,
    "1 MB": 1024 * 1024
}

# Size selection UI
preset_choice = st.selectbox("Choose target file size:", list(size_presets.keys()), index=2)
custom_size_kb = st.number_input("Or enter your own size (KB):", value=size_presets[preset_choice] // 1024, step=50)
target_size = int(custom_size_kb * 1024)  # Convert to bytes

# Upload multiple files
uploaded_files = st.file_uploader(
    "Upload your images", 
    type=[ext.replace('.', '') for ext in allowed_extensions], 
    accept_multiple_files=True
)

# Resize function
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

if uploaded_files:
    # Prepare ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file in uploaded_files:
            try:
                img = Image.open(file).convert("RGB")
                img = resize_image(img, max_width, max_height)

                # Compress until within target size
                temp_quality = initial_quality
                img_bytes = io.BytesIO()

                while temp_quality >= min_quality:
                    img_bytes.seek(0)
                    img.save(img_bytes, 'webp', quality=temp_quality)
                    size = img_bytes.tell()
                    if size <= target_size:
                        break
                    temp_quality -= quality_step

                # Add to ZIP
                img_bytes.seek(0)
                output_filename = file.name.rsplit(".", 1)[0] + ".webp"
                zip_file.writestr(output_filename, img_bytes.read())

            except Exception as e:
                st.error(f"❌ Error processing {file.name}: {e}")

    zip_buffer.seek(0)
    st.download_button(
        label="📥 Download All Converted Images (ZIP)",
        data=zip_buffer,
        file_name="converted_images.zip",
        mime="application/zip"
    )
