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

IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# === Step 1: Choose how to start ===
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

# === Step 2: Photo Capture + Preview ===
st.subheader("Step 1: Take or Upload a Photo")

if st.session_state["image_data"] is None:
    col1, col2 = st.columns(2)
    with col1:
        camera = st.camera_input("Take a photo")
    with col2:
        upload = st.file_uploader("Or upload from device", type=["jpg", "jpeg", "png"])

    if camera or upload:
        st.session_state["image_data"] = camera or upload
        st.experimental_rerun()

# === Step 3: Large Preview + Option to Retake ===
if st.session_state["image_data"] is not None:
    st.image(st.session_state["image_data"], caption="Captured Photo", use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔁 Retake Photo"):
            st.session_state["image_data"] = None
            st.experimental_rerun()
    with col2:
        st.success("Photo captured. Proceed to fill in data.")

# === Step 4: Data Entry Form ===
if st.session_state["image_data"] is not None and st.session_state["columns"]:
    st.subheader("Step 2: Enter Data for Photo")
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

            # Prepare download buffer
            buffer = BytesIO()
            image.save(buffer, format="JPEG")
            buffer.seek(0)
            st.session_state["photo_ready"] = True
            st.session_state["photo_buffer"] = buffer
            st.session_state["photo_filename"] = filename

            # Reset image data
            st.session_state["image_data"] = None

            st.success("Entry added. Scroll down to download.")

# === Step 5: Photo + CSV Downloads ===
if st.session_state.get("photo_ready"):
    st.download_button(
        label="📥 Download Photo",
        data=st.session_state["photo_buffer"],
        file_name=st.session_state["photo_filename"],
        mime="image/jpeg"
    )
    st.session_state["photo_ready"] = False

# === Step 6: Show Table + CSV Download ===
df = st.session_state.get("df", None)
if df is not None and not df.empty:
    st.subheader("📄 Updated Data Table")
    st.dataframe(df)

    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    st.download_button(
        label="⬇️ Download Updated CSV",
        data=csv_buffer,
        file_name="updated_data.csv",
        mime="text/csv"
    )

    st.subheader("🖼️ Most Recent Image")
    last_file = df.iloc[-1]["image_filename"]
    image_path = os.path.join(IMAGE_DIR, last_file)
    if os.path.exists(image_path):
        st.image(image_path, caption=last_file, use_container_width=True)
