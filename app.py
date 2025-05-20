import streamlit as st
import pandas as pd
import os
from PIL import Image
from datetime import datetime
from io import BytesIO

# App title
st.set_page_config(page_title="Photo Data Capture")
st.title("📸 Photo Data Capture")
st.info("Upload a CSV file from your phone, Google Drive, or OneDrive to start.")

# Image directory (used for session, not persistent in cloud)
IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# Step 1: Upload CSV file
uploaded_csv = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_csv:
    # Load CSV into DataFrame
    df = pd.read_csv(uploaded_csv)

    # Add 'image_filename' column if missing
    if "image_filename" not in df.columns:
        df["image_filename"] = ""

    # Use all columns except image reference for data entry
    columns = [col for col in df.columns if col != "image_filename"]
    st.success("CSV loaded with fields: " + ", ".join(columns))

    # Step 2: Data entry form
    st.header("➕ Add a New Entry")
    entry_data = {}

    with st.form("entry_form"):
        for col in columns:
            entry_data[col] = st.text_input(col)

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

                # Save photo to server
                image = Image.open(image_data)
                image.save(filepath)

                # Append new row
                new_row = entry_data.copy()
                new_row["image_filename"] = filename
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                st.success("Entry added!")

                # Offer photo download
                img_buffer = BytesIO()
                image.save(img_buffer, format="JPEG")
                img_buffer.seek(0)

                st.download_button(
                    label="📥 Download Photo",
                    data=img_buffer,
                    file_name=filename,
                    mime="image/jpeg"
                )

    # Step 3: Show table and offer CSV download
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

    # Step 4: Show most recent image
    st.subheader("🖼️ Most Recent Image")
    if not df.empty:
        last_filename = df.iloc[-1]["image_filename"]
        image_path = os.path.join(IMAGE_DIR, last_filename)
        if os.path.exists(image_path):
            st.image(image_path, caption=last_filename, use_column_width=True)
