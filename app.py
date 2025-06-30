# app.py

import streamlit as st
import whitebox
import os
from tempfile import NamedTemporaryFile
import rasterio
import matplotlib.pyplot as plt

# Initialize WhiteboxTools
wbt = whitebox.WhiteboxTools()
wbt.set_whitebox_dir("tools/WBT")  # path to the binary
wbt.verbose = True  # Enable verbose output for debugging

st.title("DEM Hillshade Generator using WhiteboxTools")

# Upload DEM
uploaded_file = st.file_uploader("Upload a DEM file (GeoTIFF)", type=["tif", "tiff"])

if uploaded_file:
    with NamedTemporaryFile(delete=False, suffix=".tif") as tmp_input:
        tmp_input.write(uploaded_file.read())
        input_path = tmp_input.name

    output_path = input_path.replace(".tif", "_hillshade.tif")

    # Run Hillshade
    st.write("Generating hillshade...")
    try:
        wbt.hillshade(
            dem=input_path,
            output=output_path,
            azimuth=315.0,
            altitude=45.0
        )
    except Exception as e:
        st.error(f"WhiteboxTools failed: {e}")
        st.stop()

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
