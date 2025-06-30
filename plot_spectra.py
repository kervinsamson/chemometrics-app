#
# plot_spectra_gui.py
#
# Description:
# GUI app to:
# - select .spa files
# - display spectra
# - allow entering numeric values for each file (future regression target)
# - switch between original spectra, 1st derivative, and 2nd derivative
# - return to Home to select new files
#
# Author: Kervin Ralph A. Samson
# Date: 06/26/2025
#

import os
import numpy as np
import spectrochempy as spc
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class SpectraViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Spectra Viewer")

        # Initialize data
        self.file_paths = []
        self.filenames = []
        self.spectra_data = None
        self.first_derivatives = None
        self.second_derivatives = None
        self.wavenumbers = None

        self.user_values = {}

        # Create GUI layout
        self.create_widgets()

    def create_widgets(self):
        # Frame for file operations
        top_frame = tk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        btn_load_all = tk.Button(top_frame, text="Load All .spa Files from Folder", command=self.load_all_files_from_folder)
        btn_load_all.pack(side=tk.LEFT, padx=5, pady=5)

        btn_select_files = tk.Button(top_frame, text="Select Specific Files", command=self.select_files)
        btn_select_files.pack(side=tk.LEFT, padx=5, pady=5)

        btn_plot = tk.Button(top_frame, text="Plot Spectra", command=self.plot_original)
        btn_plot.pack(side=tk.LEFT, padx=5, pady=5)

        btn_deriv1 = tk.Button(top_frame, text="1st Derivative", command=self.plot_derivative1)
        btn_deriv1.pack(side=tk.LEFT, padx=5, pady=5)

        btn_deriv2 = tk.Button(top_frame, text="2nd Derivative", command=self.plot_derivative2)
        btn_deriv2.pack(side=tk.LEFT, padx=5, pady=5)

        btn_home = tk.Button(top_frame, text="Reset", command=self.go_home)
        btn_home.pack(side=tk.LEFT, padx=5, pady=5)

        # Split frame for table + plot
        middle_frame = tk.Frame(self.root)
        middle_frame.pack(fill=tk.BOTH, expand=True)

        # Table frame
        table_frame = tk.Frame(middle_frame)
        table_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        tk.Label(table_frame, text="Loaded Files & Target Values").pack()

        columns = ("Filename", "Value")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        self.tree.heading("Filename", text="Filename")
        self.tree.heading("Value", text="Target Value")

        self.tree.column("Filename", width=200, anchor=tk.W)
        self.tree.column("Value", width=100, anchor=tk.CENTER)

        self.tree.pack(fill=tk.Y)

        self.tree.bind('<Double-1>', self.on_double_click)

        # Plot frame
        plot_frame = tk.Frame(middle_frame)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.figure, self.ax = plt.subplots(figsize=(7, 5))
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def load_all_files_from_folder(self):
        folder_path = filedialog.askdirectory(title="Select folder containing .spa files")
        if not folder_path:
            return

        file_paths = [
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.lower().endswith(".spa")
        ]

        if not file_paths:
            messagebox.showerror("No Files", "No .spa files found in the selected folder.")
            return

        self.load_files_from_paths(file_paths)

    def select_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Select one or more .spa files",
            filetypes=[("Spectra files", "*.spa")]
        )
        if not file_paths:
            return

        self.load_files_from_paths(file_paths)

    def load_files_from_paths(self, file_paths):
        # Reset previous data
        self.file_paths = list(file_paths)
        self.filenames = []
        self.spectra_data = []
        self.wavenumbers = None
        self.user_values = {}

        for path in self.file_paths:
            try:
                nd = spc.read_spa(path)
                intensity = nd.data.squeeze()

                if self.wavenumbers is None:
                    self.wavenumbers = nd.x.data

                if intensity.shape != nd.x.data.shape:
                    print(f"Skipping {os.path.basename(path)} due to shape mismatch.")
                    continue

                self.spectra_data.append(intensity)
                self.filenames.append(os.path.basename(path))
                self.user_values[os.path.basename(path)] = 0.0

            except Exception as e:
                print(f"Error reading {path}: {e}")

        if not self.spectra_data:
            messagebox.showerror("Error", "No valid spectra loaded.")
            return

        self.spectra_data = np.vstack(self.spectra_data)
        self.first_derivatives = np.gradient(self.spectra_data, axis=1)
        self.second_derivatives = np.gradient(self.first_derivatives, axis=1)

        self.populate_table()
        self.plot_original()

    def populate_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for filename in self.filenames:
            val = self.user_values.get(filename, 0.0)
            self.tree.insert("", tk.END, values=(filename, val))

    def on_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)

        if column == "#2":
            item = self.tree.item(row)
            current_val = item["values"][1]
            filename = item["values"][0]

            new_val = self.prompt_for_value(current_val)
            if new_val is not None:
                self.tree.set(row, "Value", new_val)
                self.user_values[filename] = float(new_val)

    def prompt_for_value(self, current_val):
        popup = tk.Toplevel(self.root)
        popup.title("Edit Value")

        tk.Label(popup, text="Enter new value:").pack(padx=10, pady=5)
        entry = tk.Entry(popup)
        entry.pack(padx=10, pady=5)
        entry.insert(0, str(current_val))

        val = None

        def confirm():
            nonlocal val
            try:
                val = float(entry.get())
                popup.destroy()
            except ValueError:
                messagebox.showerror("Invalid input", "Please enter a numeric value.")

        btn = tk.Button(popup, text="OK", command=confirm)
        btn.pack(pady=5)

        popup.grab_set()
        self.root.wait_window(popup)
        return val

    def plot_original(self):
        if self.spectra_data is None:
            return
        self.plot_data(self.spectra_data, "(Original Spectra)")

    def plot_derivative1(self):
        if self.first_derivatives is None:
            return
        self.plot_data(self.first_derivatives, "(1st Derivative)")

    def plot_derivative2(self):
        if self.second_derivatives is None:
            return
        self.plot_data(self.second_derivatives, "(2nd Derivative)")

    def plot_data(self, data, title_suffix):
        self.ax.clear()
        for i, y in enumerate(data):
            self.ax.plot(self.wavenumbers, y, label=self.filenames[i])

        self.ax.set_title(f"Spectra Viewer {title_suffix}")
        self.ax.set_xlabel("Wavenumber (cm⁻¹)")
        self.ax.set_ylabel("Absorbance / Intensity")
        self.ax.invert_xaxis()
        self.ax.set_xlim(self.wavenumbers.max(), self.wavenumbers.min())
        if len(self.filenames) <= 15:
            self.ax.legend(fontsize='small')
        self.ax.grid(True)
        self.canvas.draw()

    def go_home(self):
        self.file_paths = []
        self.filenames = []
        self.spectra_data = None
        self.first_derivatives = None
        self.second_derivatives = None
        self.wavenumbers = None
        self.user_values = {}
        self.tree.delete(*self.tree.get_children())
        self.ax.clear()
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = SpectraViewerApp(root)
    root.mainloop()
