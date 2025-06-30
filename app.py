# app.py
import streamlit as st
import os
from tempfile import NamedTemporaryFile
import rasterio
import matplotlib.pyplot as plt
import whitebox.whitebox_tools as wbt_module

# Override the download function to do nothing
wbt_module.download_wbt = lambda: None

# Now safely initialize
wbt = wbt_module.WhiteboxTools()
wbt.set_whitebox_dir("tools/WBT")
wbt.set_verbose_mode(True)

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

    
    # Check if output path is valid
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
