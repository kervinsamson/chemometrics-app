#
# plot_spectra.py
#
# Description:
# This script lets the user select one or multiple .spa spectral files
# using a GUI file picker, reads the data, and plots them on a single graph.
# It includes buttons to view the original spectra, their first derivative,
# or their second derivative. A Home button allows returning to file selection
# to add or remove files.
#
# Author: Kervin Ralph A. Samson
# Date: 06/26/2025
#

import os
import spectrochempy as spc
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import numpy as np
from tkinter import filedialog, Tk


def choose_spa_files():
    """
    Opens a GUI file dialog to let the user select .spa files.

    Returns:
        list of str: Paths to the selected files.
    """
    root = Tk()
    root.withdraw()

    file_paths = filedialog.askopenfilenames(
        title="Select one or more .spa files",
        filetypes=[("Spectra files", "*.spa")]
    )

    return list(file_paths)


def plot_spectra_from_files(file_paths):
    """
    Reads selected .spa files and plots spectra
    with buttons to view derivatives.

    Args:
        file_paths (list): List of .spa file paths.

    Returns:
        str: "home" if user clicked Home, "done" otherwise.
    """
    if not file_paths:
        print("No files selected. Exiting.")
        return "done"

    print(f"Selected {len(file_paths)} files. Loading...")

    spectra_data = []
    filenames = []

    wavenumbers = None

    for file_path in file_paths:
        try:
            filename = os.path.basename(file_path)
            nd = spc.read_spa(file_path)

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
        return "done"

    # Convert to numpy array
    spectra_data = np.vstack(spectra_data)

    # Compute derivatives
    first_derivatives = np.gradient(spectra_data, axis=1)
    second_derivatives = np.gradient(first_derivatives, axis=1)

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))
    plt.subplots_adjust(bottom=0.25)

    def plot_data(data, title_suffix):
        ax.clear()

        for i, y in enumerate(data):
            ax.plot(wavenumbers, y, label=filenames[i])

        ax.set_title(f"Spectra Viewer {title_suffix}", fontsize=16)
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

    # Buttons
    ax_original = plt.axes([0.1, 0.05, 0.15, 0.075])
    ax_deriv1 = plt.axes([0.3, 0.05, 0.2, 0.075])
    ax_deriv2 = plt.axes([0.55, 0.05, 0.2, 0.075])
    ax_home = plt.axes([0.8, 0.05, 0.15, 0.075])

    btn_original = Button(ax_original, 'Original')
    btn_deriv1 = Button(ax_deriv1, '1st Derivative')
    btn_deriv2 = Button(ax_deriv2, '2nd Derivative')
    btn_home = Button(ax_home, 'Home')

    def on_original(event):
        plot_data(spectra_data, "(Original)")

    def on_deriv1(event):
        plot_data(first_derivatives, "(1st Derivative)")

    def on_deriv2(event):
        plot_data(second_derivatives, "(2nd Derivative)")

    home_clicked = {"flag": False}

    def on_home(event):
        home_clicked["flag"] = True
        plt.close(fig)

    btn_original.on_clicked(on_original)
    btn_deriv1.on_clicked(on_deriv1)
    btn_deriv2.on_clicked(on_deriv2)
    btn_home.on_clicked(on_home)

    plt.show()

    if home_clicked["flag"]:
        return "home"
    else:
        return "done"


def run_app():
    """
    Runs the entire interactive loop of the program.
    """
    while True:
        selected_files = choose_spa_files()

        if not selected_files:
            print("No files selected. Exiting program.")
            break

        result = plot_spectra_from_files(selected_files)

        if result == "done":
            # User closed the plot or did not press Home.
            print("Exiting program.")
            break
        elif result == "home":
            # User pressed Home. Loop again.
            continue


# --- Main execution block ---
if __name__ == "__main__":
    run_app()
