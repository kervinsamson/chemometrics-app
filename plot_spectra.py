#
# plot_spectra_gui_styled_maroon_green.py
#
# Description:
# Spectra Viewer GUI with maroon header and dark green buttons.
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

        # Window background
        self.root.configure(bg="#f7f2f2")

        # Data initialization
        self.file_paths = []
        self.filenames = []
        self.spectra_data = None
        self.first_derivatives = None
        self.second_derivatives = None
        self.wavenumbers = None

        self.user_values = {}

        self.legend_visible = True          # NEW: Legend toggle flag
        self.last_plot_type = None          # NEW: track last plotted type

        self.create_styles()
        self.create_widgets()

    def create_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Treeview styling
        style.configure("Treeview",
                        background="#ffffff",
                        foreground="#333333",
                        rowheight=25,
                        fieldbackground="#ffffff",
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background="#800000",
                        foreground="white",
                        font=("Segoe UI", 11, "bold"))
        style.map("Treeview",
                  background=[("selected", "#c1e0c1")],
                  foreground=[("selected", "black")])

    def create_widgets(self):
        # Header bar
        header = tk.Label(self.root,
                          text="Spectra Viewer",
                          bg="#800000",
                          fg="white",
                          font=("Segoe UI", 18, "bold"),
                          pady=10)
        header.pack(fill=tk.X)

        # Top frame
        top_frame = tk.Frame(self.root, bg="#f7f2f2")
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        btn_params = {
            "bg": "#006400",
            "fg": "white",
            "activebackground": "#228B22",
            "activeforeground": "white",
            "font": ("Segoe UI", 10, "bold"),
            "bd": 0,
            "padx": 10,
            "pady": 5,
            "relief": tk.FLAT,
        }

        btn_load_all = tk.Button(top_frame, text="Load All .spa Files from Folder",
                                 command=self.load_all_files_from_folder, **btn_params)
        btn_load_all.pack(side=tk.LEFT, padx=5)

        btn_select_files = tk.Button(top_frame, text="Select Specific Files",
                                     command=self.select_files, **btn_params)
        btn_select_files.pack(side=tk.LEFT, padx=5)

        btn_plot = tk.Button(top_frame, text="Plot Spectra",
                             command=self.plot_original, **btn_params)
        btn_plot.pack(side=tk.LEFT, padx=5)

        btn_deriv1 = tk.Button(top_frame, text="1st Derivative",
                               command=self.plot_derivative1, **btn_params)
        btn_deriv1.pack(side=tk.LEFT, padx=5)

        btn_deriv2 = tk.Button(top_frame, text="2nd Derivative",
                               command=self.plot_derivative2, **btn_params)
        btn_deriv2.pack(side=tk.LEFT, padx=5)

        btn_home = tk.Button(top_frame, text="Reset",
                             command=self.go_home, **btn_params)
        btn_home.pack(side=tk.LEFT, padx=5)

        # NEW: Toggle Legend button
        btn_toggle_legend = tk.Button(
            top_frame,
            text="Toggle Legend",
            command=self.toggle_legend,
            **btn_params
        )
        btn_toggle_legend.pack(side=tk.LEFT, padx=5)

        # Middle layout
        middle_frame = tk.Frame(self.root, bg="#f7f2f2")
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Table frame
        table_frame = tk.Frame(middle_frame, bg="#f4e3e3", bd=2, relief=tk.GROOVE)
        table_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        label = tk.Label(table_frame,
                         text="Loaded Files & Target Values",
                         bg="#800000",
                         fg="white",
                         font=("Segoe UI", 12, "bold"),
                         pady=5)
        label.pack(fill=tk.X)

        columns = ("Filename", "Value")
        self.tree = ttk.Treeview(table_frame,
                                 columns=columns,
                                 show="headings",
                                 height=20)
        self.tree.heading("Filename", text="Filename")
        self.tree.heading("Value", text="Target Value")

        self.tree.column("Filename", width=200, anchor=tk.W)
        self.tree.column("Value", width=100, anchor=tk.CENTER)

        self.tree.pack(fill=tk.Y, padx=5, pady=5)

        self.tree.bind('<Double-1>', self.on_double_click)

        # Plot frame
        plot_frame = tk.Frame(middle_frame, bg="#ffffff", bd=2, relief=tk.RIDGE)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.figure, self.ax = plt.subplots(figsize=(7, 5))
        self.figure.patch.set_facecolor("#ffffff")
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
        popup.configure(bg="#f7f2f2")

        tk.Label(popup,
                 text="Enter new value:",
                 font=("Segoe UI", 10),
                 bg="#f7f2f2").pack(padx=10, pady=5)
        entry = tk.Entry(popup, font=("Segoe UI", 10))
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

        btn = tk.Button(popup,
                        text="OK",
                        bg="#006400",
                        fg="white",
                        activebackground="#228B22",
                        font=("Segoe UI", 10, "bold"),
                        relief=tk.FLAT,
                        command=confirm)
        btn.pack(pady=5)

        popup.grab_set()
        self.root.wait_window(popup)
        return val

    def plot_original(self):
        if self.spectra_data is None:
            return
        self.last_plot_type = "original"     # NEW
        self.plot_data(self.spectra_data, "(Original Spectra)")

    def plot_derivative1(self):
        if self.first_derivatives is None:
            return
        self.last_plot_type = "deriv1"       # NEW
        self.plot_data(self.first_derivatives, "(1st Derivative)")

    def plot_derivative2(self):
        if self.second_derivatives is None:
            return
        self.last_plot_type = "deriv2"       # NEW
        self.plot_data(self.second_derivatives, "(2nd Derivative)")

    def plot_data(self, data, title_suffix):
        self.ax.clear()
        for i, y in enumerate(data):
            self.ax.plot(self.wavenumbers, y, label=self.filenames[i])

        self.ax.set_facecolor("#ffffff")
        self.ax.set_title(f"Spectra Viewer {title_suffix}", fontsize=14, color="#800000")
        self.ax.set_xlabel("Wavenumber (cm⁻¹)", fontsize=12, color="#333333")
        self.ax.set_ylabel("Absorbance / Intensity", fontsize=12, color="#333333")
        self.ax.invert_xaxis()
        self.ax.set_xlim(self.wavenumbers.max(), self.wavenumbers.min())
        if self.legend_visible and len(self.filenames) <= 15:
            self.ax.legend(fontsize='small')
        self.ax.grid(True, color="#cccccc")
        self.canvas.draw()

    def toggle_legend(self):
        self.legend_visible = not self.legend_visible
        # Re-plot current data
        if self.spectra_data is None:
            return
        if self.last_plot_type == "original":
            self.plot_original()
        elif self.last_plot_type == "deriv1":
            self.plot_derivative1()
        elif self.last_plot_type == "deriv2":
            self.plot_derivative2()
        else:
            self.plot_original()

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
        self.last_plot_type = None

if __name__ == "__main__":
    root = tk.Tk()
    app = SpectraViewerApp(root)
    root.mainloop()
