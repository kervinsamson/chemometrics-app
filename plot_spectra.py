#
# plot_spectra.py
#
# Description:
# This script reads all .spa spectral files from a specified folder,
# extracts the spectral data correctly, and plots them all on a single graph.
# It adds buttons to view the original spectra,
# their first derivative, and second derivative.
#
# Author: Kervin Ralph A. Samson
# Date: 06/26/2025
#

import os
import glob
import spectrochempy as spc
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import numpy as np

def plot_spectra_from_folder(folder_path):
    """
    Reads all .spa files from a given folder and plots their spectra
    with buttons to view the original spectra or their derivatives.

    Args:
        folder_path (str): The path to the folder containing .spa files.

    Returns:
        None: Displays an interactive Matplotlib plot.
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

    print(f"Found {len(spa_files)} .spa files. Loading...")

    # Data containers
    spectra_data = []
    filenames = []

    wavenumbers = None

    # 3. Read all files and store data
    for file_path in spa_files:
        try:
            filename = os.path.basename(file_path)
            nd = spc.read_spa(file_path)

            # Store wavenumbers only once
            if wavenumbers is None:
                wavenumbers = nd.x.data

            intensity = nd.data.squeeze()

            if nd.x.data.shape != intensity.shape:
                print(f"Skipping {filename} due to shape mismatch: X={nd.x.data.shape}, Y={intensity.shape}")
                continue

            spectra_data.append(intensity)
            filenames.append(filename)

        except Exception as e:
            print(f"Could not process file: {file_path}. Reason: {e}")

    if not spectra_data:
        print("No valid spectra loaded.")
        return

    # Convert list to 2D NumPy array for easier manipulation
    spectra_data = np.vstack(spectra_data)

    # Derivatives
    first_derivatives = np.gradient(spectra_data, axis=1)
    second_derivatives = np.gradient(first_derivatives, axis=1)

    # 4. Set up Matplotlib plot
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))
    plt.subplots_adjust(bottom=0.2)  # Leave space for buttons

    # Helper function to plot data
    def plot_data(data, title_suffix):
        ax.clear()

        for i, y in enumerate(data):
            ax.plot(wavenumbers, y, label=filenames[i])

        ax.set_title(f"Spectra from Folder: {os.path.basename(folder_path)} {title_suffix}", fontsize=16)
        ax.set_xlabel('Wavenumber (cm⁻¹)', fontsize=12)
        ax.set_ylabel('Absorbance / Intensity', fontsize=12)
        ax.invert_xaxis()

        ax.set_xlim(wavenumbers.max(), wavenumbers.min())

        if len(filenames) <= 15:
            ax.legend(title='Files', fontsize='small')
        else:
            print("\nMore than 15 files found. Skipping legend to avoid clutter.")

        ax.grid(True)
        fig.canvas.draw_idle()

    # Initial plot
    plot_data(spectra_data, "(Original)")

    # Create buttons
    ax_original = plt.axes([0.1, 0.05, 0.15, 0.075])
    ax_deriv1 = plt.axes([0.3, 0.05, 0.2, 0.075])
    ax_deriv2 = plt.axes([0.55, 0.05, 0.2, 0.075])

    btn_original = Button(ax_original, 'Original')
    btn_deriv1 = Button(ax_deriv1, '1st Derivative')
    btn_deriv2 = Button(ax_deriv2, '2nd Derivative')

    def on_original(event):
        plot_data(spectra_data, "(Original)")

    def on_deriv1(event):
        plot_data(first_derivatives, "(1st Derivative)")

    def on_deriv2(event):
        plot_data(second_derivatives, "(2nd Derivative)")

    btn_original.on_clicked(on_original)
    btn_deriv1.on_clicked(on_deriv1)
    btn_deriv2.on_clicked(on_deriv2)

    plt.show()

# --- Main execution block ---
if __name__ == "__main__":
    path_to_data = "spa_data"
    plot_spectra_from_folder(path_to_data)
