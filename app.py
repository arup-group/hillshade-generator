# app.py
import streamlit as st
import os
import subprocess
from tempfile import NamedTemporaryFile
import rasterio
import matplotlib.pyplot as plt

st.title("DEM Hillshade Generator using WhiteboxTools")

# Upload DEM
uploaded_file = st.file_uploader("Upload a DEM file (GeoTIFF)", type=["tif", "tiff"])

if uploaded_file:
    with NamedTemporaryFile(delete=False, suffix=".tif") as tmp_input:
        tmp_input.write(uploaded_file.read())
        input_path = tmp_input.name

    output_path = input_path.replace(".tif", "_hillshade.tif")

    # Show input metadata
    try:
        with rasterio.open(input_path) as src:
            st.write("DEM metadata:", src.meta)
    except Exception as e:
        st.error(f"Failed to read DEM file: {e}")
        st.stop()

    # Run WhiteboxTools via subprocess
    st.write("Generating hillshade...")
    cmd = [
        "tools/WBT/whitebox_tools",
        "--run=Hillshade",
        f"--dem={input_path}",
        f"--output={output_path}",
        "--azimuth=315.0",
        "--altitude=45.0"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        st.text("WhiteboxTools stdout:")
        st.text(result.stdout)
        st.text("WhiteboxTools stderr:")
        st.text(result.stderr)
    except Exception as e:
        st.error(f"Failed to run whitebox_tools: {e}")
        st.stop()

    # Check if output was created
    st.write("Expected output path:", output_path)
    st.write("Output exists:", os.path.exists(output_path))

    if not os.path.exists(output_path):
        st.error("Hillshade file was not created. Please check the input DEM file.")
        st.stop()

    st.success("Hillshade generated!")

    # Display using rasterio and matplotlib
    with rasterio.open(output_path) as src:
        hillshade = src.read(1)

    fig, ax = plt.subplots()
    ax.imshow(hillshade, cmap="gray")
    ax.set_title("Hillshade Output")
    ax.axis("off")
    st.pyplot(fig)

    # Download link
    with open(output_path, "rb") as f:
        st.download_button("Download Hillshade", f, file_name="hillshade.tif")