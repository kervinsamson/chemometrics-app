#
# plot_spectra.py
#
# Description:
# This script reads all .spa spectral files from a specified folder,
# extracts the spectral data correctly, and plots them all on a single graph.
# It ensures the plot's x-axis fits the data range exactly  without extra whitespace.
#
# Author: Kervin Ralph A. Samson
# Date: 06/26/2025
#

import os
import glob
import spectrochempy as spc
import matplotlib.pyplot as plt

def plot_spectra_from_folder(folder_path):
    """
    Reads all .spa files from a given folder and plots their spectra.

    Args:
        folder_path (str): The path to the folder containing .spa files.

    Returns:
        None: Displays a Matplotlib plot.
    """
    # 1. Validate the folder path
    if not os.path.isdir(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        return

    # 2. Find all .spa files in the folder
    spa_files = glob.glob(os.path.join(folder_path, '*.spa'))

    if not spa_files:
        print(f"Error: No .spa files found in '{folder_path}'.")
        return

    print(f"Found {len(spa_files)} .spa files. Loading and plotting...")

    # 3. Set up the plot using Matplotlib
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))

    # Initialize a variable to hold the x-axis data (wavenumbers)
    # We'll get this from the first successfully read file.
    wavenumbers = None

    # 4. Loop through each file, read it, and plot it
    for file_path in spa_files:
        try:
            filename = os.path.basename(file_path)
            # Read the .spa file using SpectroChemPy
            nd = spc.read_spa(file_path)

            # Store the wavenumbers from the first successfully read file
            if wavenumbers is None:
                wavenumbers = nd.x.data

            # Get intensity data from .data and use .squeeze()
            intensity = nd.data.squeeze()

            # Final check to ensure dimensions match before plotting
            if nd.x.data.shape != intensity.shape:
                print(f"Skipping {filename} due to shape mismatch after processing: X={nd.x.data.shape}, Y={intensity.shape}")
                continue

            # Plot the data on the axes we created earlier
            ax.plot(nd.x.data, intensity, label=filename)

        except Exception as e:
            # Handle potential errors if a file is corrupted or not a valid .spa file
            print(f"Could not process file: {file_path}. Reason: {e}")

    # Customize the plot to make it publication-quality
    ax.set_title(f'Spectra from Folder: {os.path.basename(folder_path)}', fontsize=16)
    ax.set_xlabel('Wavenumber (cm⁻¹)', fontsize=12)
    ax.set_ylabel('Absorbance / Intensity', fontsize=12)

    # Invert the x-axis, which is standard practice for IR/NIR spectra
    ax.invert_xaxis()

    # Set the x-axis limits to the exact min and max of the data
    # This removes the extra whitespace at the start and end of the plot.
    # We use max() first because the axis is inverted.
    if wavenumbers is not None:
        ax.set_xlim(wavenumbers.max(), wavenumbers.min())

    # Add a legend to identify each spectrum.
    # If there are too many files, a legend can get crowded.
    if len(spa_files) <= 15:
        ax.legend(title='Files', fontsize='small')
    else:
        print("\nMore than 15 files found. Skipping legend to avoid clutter.")

    # Add grid lines for better readability
    ax.grid(True)

    # Display the plot
    plt.tight_layout() # Adjusts plot to prevent labels from overlapping
    plt.show()


# --- Main execution block ---
if __name__ == "__main__":
    # Assumes you have a folder named 'spa_data'
    # in the same directory where you save this script.
    path_to_data = "spa_data"

    plot_spectra_from_folder(path_to_data)