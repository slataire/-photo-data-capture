import streamlit as st
import pandas as pd
import os
from PIL import Image
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Photo Data Capture", layout="centered")
st.title("📸 Photo Data Capture")

# === Initialize session state ===
for key in [
    "photo_ready", "photo_buffer", "photo_filename",
    "df", "columns", "image_data"
]:
    if key not in st.session_state:
        st.session_state[key] = None

# === Set up image directory ===
IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# === Step 1: Choose data source ===
st.info("Start by uploading a CSV or defining your own data fields.")
input_method = st.radio("Input method:", ["📁 Upload CSV", "🛠️ Define fields manually"])

# === Option 1: Upload CSV ===
if input_method == "📁 Upload CSV":
    uploaded_csv = st.file_uploader("Upload your CSV file", type=["csv"])
    if uploaded_csv:
        df = pd.read_csv(uploaded_csv)
        if "image_filename" not in df.columns:
            df["image_filename"] = ""
        columns = [col for col in df.columns if col != "image_filename"]
        st.session_state["df"] = df
        st.session_state["columns"] = columns
        st.success(f"Loaded fields: {', '.join(columns)}")

# === Option 2: Define fields manually ===
elif input_method == "🛠️ Define fields manually":
    st.markdown("Enter one field name per line:")
    field_text = st.text_area("Custom fields", "Sample_ID\nDepth\nNotes")
    columns = [f.strip() for f in field_text.splitlines() if f.strip()]
    if columns:
        df = pd.DataFrame(columns=columns + ["image_filename"])
        st.session_state["df"] = df
        st.session_state["columns"] = columns
        st.success(f"Defined fields: {', '.join(columns)}")

# === Step 2: Photo capture ===
st.subheader("Step 1: Capture or Upload a Photo")

if st.session_state["image_data"] is None:
    photo_input = st.camera_input("📷 Take a photo")
    upload_input = st.file_uploader("Or upload from your device", type=["jpg", "jpeg", "png"])

    if photo_input or upload_input:
        st.session_state["image_data"] = photo_input or upload_input
        st.experimental_rerun()

# === Step 3: Preview + Retake ===
if st.session_state["image_data"] is not None:
    st.image(st.session_state["image_data"], caption="Captured Photo", use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔁 Retake Photo"):
            st.session_state["image_data"] = None
            st.experimental_rerun()
    with col2:
        st.success("Photo captured. Continue below to enter data.")

# === Step 4: Metadata entry form ===
if st.session_state["image_data"] is not None and st.session_state["columns"]:
    st.subheader("Step 2: Enter Metadata for Photo")
    entry_data = {}

    with st.form("entry_form"):
        for col in st.session_state["columns"]:
            entry_data[col] = st.text_input(f"{col}")

        submitted = st.form_submit_button("Add Entry")

        if submitted:
            image_data = st.session_state["image_data"]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}.jpg"
            filepath = os.path.join(IMAGE_DIR, filename)

            image = Image.open(image_data)
            image.save(filepath)

            new_row = entry_data.copy()
            new_row["image_filename"] = filename
            st.session_state["df"] = pd.concat(
                [st.session_state["df"], pd.DataFrame([new_row])],
                ignore_index=True
            )

            # Create download buffer for photo
            buffer = BytesIO()
            image.save(buffer, format="JPEG")
            buffer.seek(0)
            st.session_state["photo_ready"] = True
            st.session_state["photo_buffer"] = buffer
            st.session_state["photo_filename"] = filename

            # Reset photo for next entry
            st.session_state["image_data"] = None

            st.success("✅ Entry added. Scroll down to download files.")

# === Step 5: Photo download button ===
if st.session_state.get("photo_ready"):
    st.download_button(
        label="📥 Download Photo",
        data=st.session_state["photo_buffer"],
        file_name=st.session_state["photo_filename"],
        mime="image/jpeg"
    )
    st.session_state["photo_ready"] = False

# === Step 6: CSV and data table ===
df = st.session_state.get("df", None)
if df is not None and not df.empty:
    st.subheader("📄 Updated Data Table")
    st.dataframe(df)

    # CSV download
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    st.download_button(
        label="⬇️ Download Updated CSV",
        data=csv_buffer,
        file_name="updated_data.csv",
        mime="text/csv"
    )

    # Most recent image
    st.subheader("🖼️ Most Recent Image")
    last_file = df.iloc[-1]["image_filename"]
    image_path = os.path.join(IMAGE_DIR, last_file)
    if os.path.exists(image_path):
        st.image(image_path, caption=last_file, use_container_width=True)

