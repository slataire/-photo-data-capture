import streamlit as st
import pandas as pd
import os
from PIL import Image
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Photo Data Capture", layout="centered")
st.title("📸 Photo Data Capture")

# === Initialize session state ===
for key in ["photo_ready", "photo_buffer", "photo_filename"]:
    if key not in st.session_state:
        st.session_state[key] = None

# === Ensure image directory exists ===
IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# === Choose CSV upload or manual field creation ===
st.info("Start by uploading a CSV or defining your own data fields.")
input_method = st.radio("Input method:", ["📁 Upload CSV", "🛠️ Define fields manually"])

df = None
columns = []

# === Option 1: Upload CSV ===
if input_method == "📁 Upload CSV":
    uploaded_csv = st.file_uploader("Upload your CSV file", type=["csv"])
    if uploaded_csv:
        df = pd.read_csv(uploaded_csv)
        if "image_filename" not in df.columns:
            df["image_filename"] = ""
        columns = [col for col in df.columns if col != "image_filename"]
        st.success(f"Loaded fields: {', '.join(columns)}")

# === Option 2: Manual Field Creation ===
elif input_method == "🛠️ Define fields manually":
    st.markdown("Enter one field name per line:")
    field_text = st.text_area("Custom fields", "Sample_ID\nDepth\nNotes")
    columns = [f.strip() for f in field_text.splitlines() if f.strip()]
    if columns:
        df = pd.DataFrame(columns=columns + ["image_filename"])
        st.success(f"Defined fields: {', '.join(columns)}")

# === Data entry form ===
if df is not None and columns:
    st.header("➕ Add a New Entry")
    entry_data = {}

    with st.form("entry_form"):
        for col in columns:
            entry_data[col] = st.text_input(f"{col}")

        photo = st.camera_input("Take a photo (or upload below)")
        upload = st.file_uploader("Or upload a photo", type=["jpg", "jpeg", "png"])
        submitted = st.form_submit_button("Add Entry")

        if submitted:
            if not photo and not upload:
                st.error("Please provide a photo.")
            else:
                image_data = photo or upload
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}.jpg"
                filepath = os.path.join(IMAGE_DIR, filename)

                image = Image.open(image_data)
                image.save(filepath)

                # Append to dataframe
                new_row = entry_data.copy()
                new_row["image_filename"] = filename
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                st.success("Entry added.")

                # Prepare image for download
                img_buffer = BytesIO()
                image.save(img_buffer, format="JPEG")
                img_buffer.seek(0)

                # Store in session state for download outside form
                st.session_state["photo_ready"] = True
                st.session_state["photo_buffer"] = img_buffer
                st.session_state["photo_filename"] = filename

# === Photo download button (must be outside form) ===
if st.session_state.get("photo_ready"):
    st.download_button(
        label="📥 Download Photo",
        data=st.session_state["photo_buffer"],
        file_name=st.session_state["photo_filename"],
        mime="image/jpeg"
    )
    st.session_state["photo_ready"] = False

# === Updated Data Table + CSV Download ===
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

    # === Show most recent photo larger ===
    st.subheader("🖼️ Most Recent Image")
    last_photo = df.iloc[-1]["image_filename"]
    image_path = os.path.join(IMAGE_DIR, last_photo)
    if os.path.exists(image_path):
        st.image(image_path, caption=last_photo, use_container_width=True)

