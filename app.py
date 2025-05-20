import streamlit as st
import pandas as pd
import os
from PIL import Image
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Photo Data Capture")
st.title("📸 Photo Data Capture")

IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# Choose input method
st.info("Start by uploading a CSV or defining your own data fields.")
option = st.radio("Choose input method:", ["📁 Upload CSV", "🛠️ Define fields manually"])

df = None
columns = []

# === Option 1: Upload CSV ===
if option == "📁 Upload CSV":
    uploaded_csv = st.file_uploader("Upload your CSV file", type=["csv"])
    if uploaded_csv:
        df = pd.read_csv(uploaded_csv)
        if "image_filename" not in df.columns:
            df["image_filename"] = ""
        columns = [col for col in df.columns if col != "image_filename"]
        st.success(f"Loaded CSV with fields: {', '.join(columns)}")

# === Option 2: Define Fields Manually ===
elif option == "🛠️ Define fields manually":
    st.markdown("Enter custom field names (e.g., Sample_ID, Depth, Notes)")
    field_input = st.text_area("One field per line:", "Sample_ID\nDepth\nNotes")
    columns = [f.strip() for f in field_input.split("\n") if f.strip()]
    if columns:
        df = pd.DataFrame(columns=columns + ["image_filename"])
        st.success(f"Defined fields: {', '.join(columns)}")

# === Data Entry Form ===
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

                # Save image to server
                image = Image.open(image_data)
                image.save(filepath)

                # Add new row
                new_row = entry_data.copy()
                new_row["image_filename"] = filename
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                st.success("Entry added!")

                # Offer image download
                try:
                    img_buffer = BytesIO()
                    image.save(img_buffer, format="JPEG")
                    img_buffer.seek(0)

                    st.download_button(
                        label="📥 Download Photo",
                        data=img_buffer,
                        file_name=filename,
                        mime="image/jpeg"
                    )
                except Exception as e:
                    st.warning(f"Could not offer photo download: {e}")

    # Display table and CSV download
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

    # Show last photo
    st.subheader("🖼️ Last Image")
    if not df.empty:
        last_file = df.iloc[-1]["image_filename"]
        image_path = os.path.join(IMAGE_DIR, last_file)
        if os.path.exists(image_path):
            st.image(image_path, caption=last_file, use_column_width=True)
