import streamlit as st
import os
import subprocess
import stat
from tempfile import NamedTemporaryFile
import rasterio
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
from pysheds.grid import Grid

st.title("DEM Hillshade, Flow Direction & Accumulation Visualizer")

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

    # Ensure whitebox_tools is executable
    binary_path = "tools/WBT/whitebox_tools"
    if not os.access(binary_path, os.X_OK):
        try:
            os.chmod(binary_path, os.stat(binary_path).st_mode | stat.S_IEXEC)
        except Exception as e:
            st.error(f"Failed to set executable permission: {e}")
            st.stop()

    # Run WhiteboxTools via subprocess
    st.write("Generating hillshade...")
    cmd = [
        binary_path,
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

    if not os.path.exists(output_path):
        st.error("Hillshade file was not created. Please check the input DEM file.")
        st.stop()

    st.success("Hillshade generated!")

    # Display hillshade
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

    # -------------------------------
    # PySheds Flow Accumulation & Direction
    # -------------------------------
    st.write("Computing flow direction and accumulation with PySheds...")

    try:
        # Initialize grid and read DEM once
        grid = Grid.from_raster(input_path)
        with rasterio.open(input_path) as src:
            dem = src.read(1)

        # Condition DEM
        pit_filled = grid.fill_pits(dem)
        depression_filled = grid.fill_depressions(pit_filled)
        inflated = grid.resolve_flats(depression_filled)

        # D8 direction mapping
        dirmap = (64, 128, 1, 2, 4, 8, 16, 32)

        # Compute flow direction
        grid.flowdir(inflated, dirmap=dirmap, out_name='dir', nodata_out=np.int32(-1))

        # Compute flow accumulation
        grid.accumulation(data='dir', out_name='acc')

        # View results
        fdir = grid.view('dir', nodata=np.nan)
        acc = grid.view('acc', nodata=np.nan)

        # Flow Direction Plot
        fig_fd, ax_fd = plt.subplots(figsize=(8, 6))
        fig_fd.patch.set_alpha(0)
        im_fd = ax_fd.imshow(fdir, extent=grid.extent, cmap='viridis', zorder=2)
        boundaries = [0] + sorted(list(dirmap))
        plt.colorbar(im_fd, ax=ax_fd, boundaries=boundaries, values=sorted(dirmap))
        ax_fd.set_xlabel('Longitude')
        ax_fd.set_ylabel('Latitude')
        ax_fd.set_title('Flow Direction Grid')
        ax_fd.grid(zorder=-1)
        plt.tight_layout()
        st.pyplot(fig_fd)

        # Flow Accumulation Plot
        fig_acc, ax_acc = plt.subplots(figsize=(8, 6))
        fig_acc.patch.set_alpha(0)
        ax_acc.grid(True, zorder=0)
        im_acc = ax_acc.imshow(acc, extent=grid.extent, zorder=2,
                               cmap='cubehelix',
                               norm=colors.LogNorm(vmin=1, vmax=np.nanmax(acc)),
                               interpolation='bilinear')
        plt.colorbar(im_acc, ax=ax_acc, label='Upstream Cells')
        ax_acc.set_title('Flow Accumulation')
        ax_acc.set_xlabel('Longitude')
        ax_acc.set_ylabel('Latitude')
        plt.tight_layout()
        st.pyplot(fig_acc)

    except Exception as e:
        st.error(f"PySheds processing failed: {e}")