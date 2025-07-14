import sys
import os
import csv
import joblib
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog,
    QSplitter, QGridLayout, QLabel, QHeaderView, QMessageBox,
    QSpinBox, QTabWidget, QComboBox, QLineEdit, QTextEdit, QCheckBox, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QTextOption

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar


# -----------------------------------------------------------------------------
# Import application logic and styling modules
# -----------------------------------------------------------------------------
# These imports bring in the core data processing, prediction, and UI styling logic.
from logic.processing import (
    load_spectra_from_folder, load_selected_spa_files, train_pls_model, get_processed_intensity, find_optimal_pls_components,
    save_complete_project, load_complete_project, reconstruct_spectra_data,
    load_csv_spectral_data, load_csv_folder_spectral_data, export_spa_to_csv_individual, export_spa_to_csv_combined
)
from logic.prediction_logic import predict_from_model
from .stylesheet import UP_MAROON, UP_FOREST_GREEN, UP_WHITE, UP_LIGHT_GRAY, UP_DARK_GRAY, STYLESHEET


# -----------------------------------------------------------------------------
# Main Application Window: SpectraViewer
# -----------------------------------------------------------------------------
# This class implements the main window for the IRIS-UPLB Chemometrics application.
# It provides the user interface for calibration, component management, and prediction workflows.
class SpectraViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IRIS")
        self.setGeometry(100, 100, 1600, 900)

        # --- Application State Variables ---
        self.spectra_data = {}  # Loaded spectral data
        self.chemical_components = []  # List of chemical components
        self.pls_models = {}  # Trained PLS models
        self.current_derivative = 0  # Current derivative order for display
        self.legend_visible = True  # Whether the plot legend is visible
        self.current_folder_path = None  # Store current folder path for reference

        # Model performance metrics: {comp_name: {'r2_cv': float, 'rmsecv': float}}
        self.model_performance = {}

        # Region selection state
        self.wavenumbers = None
        self.region_start = None
        self.region_end = None

        # Prediction tab state
        self.prediction_model = None
        self.prediction_spectra = {}
        self.prediction_results = {}

        # Auto PLS component selection flag
        self.auto_pls_components = False

        # --- UI Setup ---
        self.tabs = QTabWidget()
        # Set tab position to ensure consistent appearance across platforms
        self.tabs.setTabPosition(QTabWidget.North)  # Use North for top tabs
        # Align tabs to the left (default behavior, but making it explicit)
        self.tabs.setUsesScrollButtons(True)
        # Ensure tabs are left-aligned on macOS
        self.tabs.setDocumentMode(True)
        self.setCentralWidget(self.tabs)
        self.calibration_tab = self._create_calibration_tab()
        self.components_tab = self._create_components_tab()
        self.prediction_tab = self._create_prediction_tab()
        self.tabs.addTab(self.calibration_tab, "Calibration")
        self.tabs.addTab(self.components_tab, "Components")
        self.tabs.addTab(self.prediction_tab, "Prediction")

        # Connect component selector change to performance display update
        self.component_selector_combo.currentIndexChanged.connect(self.update_performance_display)

    def _create_components_tab(self):
        # This method is unchanged
        container = QWidget()
        layout = QVBoxLayout(container); layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel("Define Chemical Components & Model Parameters"); title.setObjectName("TabTitle") # Changed Title
        
        # --- NEW: Add auto PLS component selection checkbox ---
        self.auto_pls_checkbox = QCheckBox("Auto-select optimal PLS components")
        self.auto_pls_checkbox.toggled.connect(self.toggle_auto_pls_components)
        # --- END NEW ---
        
        self.components_table = QTableWidget()
        # --- MODIFIED: Add columns for PLS components and CV folds ---
        self.components_table.setColumnCount(5)
        self.components_table.setHorizontalHeaderLabels([
            "Component Name", "Abbreviation", "Unit", "PLS Components", "CV Folds"
        ])
        # --- END MODIFIED ---
        self.components_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        btn_layout = QHBoxLayout()
        self.btn_add_component = QPushButton("Add New Component")
        self.btn_remove_component = QPushButton("Remove Selected Component")
        btn_layout.addWidget(self.btn_add_component); btn_layout.addWidget(self.btn_remove_component)
        btn_layout.addStretch()
        layout.addWidget(title); layout.addWidget(self.auto_pls_checkbox); layout.addWidget(self.components_table); layout.addLayout(btn_layout); layout.addStretch()
        self.btn_add_component.clicked.connect(self.add_component)
        self.btn_remove_component.clicked.connect(self.remove_component)
        self.components_table.itemChanged.connect(self.update_component_value)
        return container

    def _create_calibration_tab(self):
        main_widget = QWidget()
        main_splitter = QSplitter(Qt.Horizontal, main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.addWidget(main_splitter)
        main_layout.setContentsMargins(0,0,0,0)

        left_panel = QWidget(); left_panel.setObjectName("ControlPanel")
        lp_layout = QVBoxLayout(left_panel); lp_layout.setContentsMargins(15, 15, 15, 15); lp_layout.setSpacing(6)
        
        # Create a scroll area for the left panel
        scroll_area = QScrollArea()
        scroll_area.setWidget(left_panel)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setObjectName("ControlPanelScrollArea")
        
        # --- MODIFIED: Simplified Training Controls ---
        train_layout = QGridLayout(); train_layout.setSpacing(6)
        self.btn_load_folder = QPushButton("1. Load Spectra (.spa or .csv)")
        lbl_step2 = QLabel("2. Enter Reference Values in Table"); lbl_step2.setObjectName("PerfLabel")
        lbl_step3 = QLabel("3. Define Components in 'Components' Tab"); lbl_step3.setObjectName("PerfLabel")
        self.btn_train_pls = QPushButton("4. Train All Models") # Changed text and step number

        train_layout.addWidget(self.btn_load_folder, 0, 0, 1, 2)
        train_layout.addWidget(lbl_step2, 1, 0, 1, 2)
        train_layout.addWidget(lbl_step3, 2, 0, 1, 2)
        train_layout.addWidget(self.btn_train_pls, 3, 0, 1, 2) # Moved to row 3
        # --- END MODIFIED ---

        # --- NEW: Import/Export Controls ---
        io_header_label = QLabel("Project Management"); io_header_label.setObjectName("PanelHeaderLabel")
        io_layout = QGridLayout(); io_layout.setSpacing(6)
        self.btn_save_complete_project = QPushButton("Save Complete Project")
        self.btn_load_complete_project = QPushButton("Load Complete Project")
        io_layout.addWidget(self.btn_save_complete_project, 0, 0)
        io_layout.addWidget(self.btn_load_complete_project, 0, 1)
        # --- END NEW ---

        # --- Region Selection / Zoom Controls (Unchanged) ---
        region_header_label = QLabel("Region Selection / Zoom"); region_header_label.setObjectName("PanelHeaderLabel")
        region_layout = QGridLayout(); region_layout.setSpacing(6)
        
        lbl_start = QLabel("Start (cm⁻¹):"); lbl_start.setObjectName("PerfLabel")
        self.start_region_input = QLineEdit(); self.start_region_input.setPlaceholderText("e.g., 3000")
        
        lbl_end = QLabel("End (cm⁻¹):"); lbl_end.setObjectName("PerfLabel")
        self.end_region_input = QLineEdit(); self.end_region_input.setPlaceholderText("e.g., 2800")

        self.btn_apply_region = QPushButton("Apply Region")
        self.btn_reset_region = QPushButton("Reset Region")
        
        region_layout.addWidget(lbl_start, 0, 0); region_layout.addWidget(self.start_region_input, 0, 1)
        region_layout.addWidget(lbl_end, 1, 0); region_layout.addWidget(self.end_region_input, 1, 1)
        region_layout.addWidget(self.btn_apply_region, 2, 0); region_layout.addWidget(self.btn_reset_region, 2, 1)
        # --- END NEW ---

        # --- MODIFIED: Calibration Data header (simplified) ---
        table_header_label = QLabel("Calibration Data"); table_header_label.setObjectName("PanelHeaderLabel")
        
        # --- NEW: Calibration Data CSV Import/Export buttons ---
        csv_layout = QGridLayout(); csv_layout.setSpacing(6)
        self.btn_import_calibration_csv = QPushButton("Import CSV")
        self.btn_export_calibration_csv = QPushButton("Export CSV")
        csv_layout.addWidget(self.btn_import_calibration_csv, 0, 0)
        csv_layout.addWidget(self.btn_export_calibration_csv, 0, 1)
        # --- END NEW ---
        
        self.data_table = QTableWidget(); self.data_table.itemChanged.connect(self.update_reference_value)
        # Set size policy to allow vertical resizing
        self.data_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # --- MODIFIED: Performance display now linked to the component selector ---
        perf_label = QLabel("Model Performance"); perf_label.setObjectName("PanelHeaderLabel")
        perf_layout = QGridLayout()
        # Add the component selector here to choose which model's performance to view
        lbl_perf_comp = QLabel("Show Performance For:"); lbl_perf_comp.setObjectName("PerfLabel")
        self.component_selector_combo = QComboBox(); self.component_selector_combo.setObjectName("ComboBox")
        self.lbl_r2, self.lbl_rmse = QLabel("R² (CV): N/A"), QLabel("RMSECV: N/A")
        self.lbl_r2.setObjectName("PerfLabel"); self.lbl_rmse.setObjectName("PerfLabel")
        # Add the export model button below the performance metrics
        self.btn_export_model = QPushButton("Export Model for Prediction")
        perf_layout.addWidget(lbl_perf_comp, 0, 0)
        perf_layout.addWidget(self.component_selector_combo, 0, 1)
        perf_layout.addWidget(self.lbl_r2, 1, 0)
        perf_layout.addWidget(self.lbl_rmse, 1, 1)
        perf_layout.addWidget(self.btn_export_model, 2, 0, 1, 2)  # Span across both columns
        # --- END MODIFIED ---
        
        # --- MODIFIED: Assemble the left panel with the new section ---
        lp_layout.addLayout(train_layout)
        lp_layout.addWidget(io_header_label)
        lp_layout.addLayout(io_layout)
        lp_layout.addWidget(region_header_label)
        lp_layout.addLayout(region_layout)
        lp_layout.addWidget(table_header_label)
        lp_layout.addLayout(csv_layout)
        lp_layout.addWidget(self.data_table)
        lp_layout.addWidget(perf_label)
        lp_layout.addLayout(perf_layout)

        # --- MODIFIED: Connect all button signals ---
        self.btn_load_folder.clicked.connect(self.load_spectra)
        self.btn_train_pls.clicked.connect(self.train_pls_model_action)
        self.btn_save_complete_project.clicked.connect(self.save_complete_project)
        self.btn_load_complete_project.clicked.connect(self.load_complete_project)
        self.btn_export_model.clicked.connect(self.export_model_for_prediction)
        self.btn_apply_region.clicked.connect(self.apply_region)
        self.btn_reset_region.clicked.connect(self.reset_region_view)
        self.btn_import_calibration_csv.clicked.connect(self.import_calibration_csv)
        self.btn_export_calibration_csv.clicked.connect(self.export_calibration_csv)
        
        right_panel = self._create_plot_panel()
        main_splitter.addWidget(scroll_area)
        main_splitter.addWidget(right_panel)
        main_splitter.setStretchFactor(0, 1); main_splitter.setStretchFactor(1, 2)
        return main_widget

    # --- NEW: Method to create the entire Prediction Tab ---
    def _create_prediction_tab(self):
        main_widget = QWidget()
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # Left Panel for Controls
        control_panel = QWidget(); control_panel.setObjectName("ControlPanel")
        cp_layout = QVBoxLayout(control_panel); cp_layout.setContentsMargins(15, 15, 15, 15); cp_layout.setSpacing(15)
        
        title = QLabel("Prediction Workflow"); title.setObjectName("PanelHeaderLabel")

        # Model Loading Section
        model_layout = QVBoxLayout()
        self.btn_load_pred_model = QPushButton("1. Load Model (.pkl)")
        self.lbl_loaded_model = QLabel("No model loaded."); self.lbl_loaded_model.setObjectName("PerfLabel")
        model_layout.addWidget(self.btn_load_pred_model)
        model_layout.addWidget(self.lbl_loaded_model)

        # Spectra Loading Section
        spectra_layout = QVBoxLayout()
        self.btn_load_pred_spectra = QPushButton("2. Load Spectra for Prediction")
        self.lbl_loaded_spectra = QLabel("No spectra loaded."); self.lbl_loaded_spectra.setObjectName("PerfLabel")
        spectra_layout.addWidget(self.btn_load_pred_spectra)
        spectra_layout.addWidget(self.lbl_loaded_spectra)

        # Run Prediction Button
        self.btn_run_prediction = QPushButton("3. Run Prediction")
        self.btn_run_prediction.setObjectName("RunButton") # Make it stand out

        cp_layout.addWidget(title)
        cp_layout.addLayout(model_layout)
        cp_layout.addLayout(spectra_layout)
        cp_layout.addWidget(self.btn_run_prediction)
        cp_layout.addStretch()

        # Right Panel for Results Table
        results_panel = QWidget()
        results_panel.setObjectName("ResultsPanel") # NEW: Add object name
        rp_layout = QVBoxLayout(results_panel)
        
        # --- MODIFIED: Results header with Export CSV button ---
        results_header_layout = QHBoxLayout()
        results_title = QLabel("Prediction Results"); results_title.setObjectName("PanelHeaderLabel")
        self.btn_export_prediction_csv = QPushButton("Export CSV")
        self.btn_export_prediction_csv.setMaximumWidth(100)
        results_header_layout.addWidget(results_title)
        results_header_layout.addStretch()
        results_header_layout.addWidget(self.btn_export_prediction_csv)
        
        self.prediction_table = QTableWidget()
        self.prediction_table.setObjectName("PredictionTable") # Add object name for specific styling
        self.prediction_table.setEditTriggers(QTableWidget.NoEditTriggers) # Make table read-only
        rp_layout.addLayout(results_header_layout)
        rp_layout.addWidget(self.prediction_table)

        layout.addWidget(control_panel, 1) # 1/3 of the space
        layout.addWidget(results_panel, 2) # 2/3 of the space

        # Connect signals
        self.btn_load_pred_model.clicked.connect(self.load_prediction_model)
        self.btn_load_pred_spectra.clicked.connect(self.load_prediction_spectra)
        self.btn_run_prediction.clicked.connect(self.run_prediction)
        self.btn_export_prediction_csv.clicked.connect(self.export_prediction_csv)

        return main_widget
    # --- END NEW ---

    def _create_plot_panel(self):
        # This method is unchanged
        container, layout = QWidget(), QVBoxLayout()
        self.fig = Figure(figsize=(10, 7), dpi=100, facecolor=UP_LIGHT_GRAY)
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        
        # --- NEW: Style matplotlib to ensure readable hover tooltips ---
        import matplotlib as mpl
        mpl.rcParams['axes.edgecolor'] = UP_DARK_GRAY
        mpl.rcParams['axes.labelcolor'] = UP_DARK_GRAY
        mpl.rcParams['xtick.color'] = UP_DARK_GRAY
        mpl.rcParams['ytick.color'] = UP_DARK_GRAY
        mpl.rcParams['text.color'] = UP_DARK_GRAY
        # Fix for tooltip/annotation text color - make tooltips dark text on light background
        mpl.rcParams['figure.facecolor'] = UP_LIGHT_GRAY
        mpl.rcParams['axes.facecolor'] = UP_WHITE
        mpl.rcParams['savefig.facecolor'] = UP_LIGHT_GRAY
        # Ensure tooltip text is dark and readable
        mpl.rcParams['font.size'] = 10
        mpl.rcParams['font.weight'] = 'normal'
        # Fix tooltip background and text colors specifically
        mpl.rcParams['patch.facecolor'] = UP_WHITE
        mpl.rcParams['patch.edgecolor'] = UP_DARK_GRAY
        # --- END NEW ---
        
        self.btn_reset = QPushButton("Reset Plot")
        
        # --- NEW: Make derivative buttons checkable to show active state ---
        self.btn_original = QPushButton("Original")
        self.btn_original.setCheckable(True)
        self.btn_deriv1 = QPushButton("1st Derivative")
        self.btn_deriv1.setCheckable(True)
        self.btn_deriv2 = QPushButton("2nd Derivative")
        self.btn_deriv2.setCheckable(True)
        # --- END NEW ---
        
        plot_btn_layout = QHBoxLayout()
        plot_btn_layout.addWidget(self.btn_reset)
        plot_btn_layout.addWidget(self.btn_original)
        plot_btn_layout.addWidget(self.btn_deriv1); plot_btn_layout.addWidget(self.btn_deriv2)
        self.btn_reset.clicked.connect(self.reset_plot)
        self.btn_original.clicked.connect(lambda: self.apply_derivative(0))
        self.btn_deriv1.clicked.connect(lambda: self.apply_derivative(1)); self.btn_deriv2.clicked.connect(lambda: self.apply_derivative(2))
        self.toolbar = NavigationToolbar(self.canvas, self)
        self._style_matplotlib_toolbar()
        
        # --- NEW: Add spectral data export controls under the graph ---
        export_layout = QHBoxLayout()
        self.btn_export_spa_individual = QPushButton("Export Individual CSV")
        self.btn_export_spa_combined = QPushButton("Export Combined CSV")

        export_layout.addWidget(self.btn_export_spa_individual)
        export_layout.addWidget(self.btn_export_spa_combined)
        export_layout.addStretch()  # Push buttons to the left

        # Connect the export button signals
        self.btn_export_spa_individual.clicked.connect(self.export_spa_individual_csv)
        self.btn_export_spa_combined.clicked.connect(self.export_spa_combined_csv)
        # --- END NEW ---

        layout.addLayout(plot_btn_layout); layout.addWidget(self.toolbar); layout.addWidget(self.canvas); layout.addLayout(export_layout)
        container.setLayout(layout)
        self.reset_plot()
        self._update_derivative_display()  # Ensure initial button state is correct
        return container

    # --- NEW: Prediction Tab Methods ---
    @Slot()
    def load_prediction_model(self):
        filePath, _ = QFileDialog.getOpenFileName(
            self, "Load Prediction Model", "", "Pickle Models (*.pkl);;All Files (*)"
        )
        if not filePath:
            return
        try:
            self.prediction_model = joblib.load(filePath)
            # Basic validation
            if 'pls_models' not in self.prediction_model or 'chemical_components' not in self.prediction_model:
                raise ValueError("Invalid model file.")
            self.lbl_loaded_model.setText(f"Model: {os.path.basename(filePath)}")
            QMessageBox.information(self, "Model Loaded", "The prediction model was loaded successfully.")
        except Exception as e:
            self.prediction_model = None
            self.lbl_loaded_model.setText("No model loaded.")
            QMessageBox.critical(self, "Error", f"Failed to load the model file: {e}")

    @Slot()
    def load_prediction_spectra(self):
        """Load spectra for prediction with user-friendly options"""
        # Ask user what they want to do
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Load Spectra for Prediction")
        msg_box.setText("How would you like to load your .spa files for prediction?")
        
        folder_btn = msg_box.addButton("Load Folder", QMessageBox.ActionRole)
        files_btn = msg_box.addButton("Select Files", QMessageBox.ActionRole)
        cancel_btn = msg_box.addButton(QMessageBox.Cancel)
        
        # Set minimum width to prevent button text from being cut off
        msg_box.setStyleSheet("QMessageBox { min-width: 350px; }")
        
        msg_box.exec_()
        
        if msg_box.clickedButton() == cancel_btn:
            return
        elif msg_box.clickedButton() == folder_btn:
            # Original folder selection logic
            folder_path = QFileDialog.getExistingDirectory(self, "Select Folder of Spectra to Predict")
            if not folder_path:
                return
            # We don't need the wavenumbers here, just the spectra data
            self.prediction_spectra, _ = load_spectra_from_folder(folder_path)
            
        elif msg_box.clickedButton() == files_btn:
            # New individual file selection logic
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, 
                "Select .spa Files for Prediction", 
                "", 
                "SPA Files (*.spa);;All Files (*)"
            )
            
            if not file_paths:
                return
                
            self.prediction_spectra, _ = load_selected_spa_files(file_paths)
        
        # Common result handling for both methods
        if not self.prediction_spectra:
            self.lbl_loaded_spectra.setText("No spectra loaded.")
            QMessageBox.warning(self, "No Spectra Found", "Could not load any .spa files.")
        else:
            self.lbl_loaded_spectra.setText(f"{len(self.prediction_spectra)} spectra loaded for prediction.")
            QMessageBox.information(self, "Spectra Loaded", f"Successfully loaded {len(self.prediction_spectra)} spectra.")

    @Slot()
    def run_prediction(self):
        if self.prediction_model is None:
            QMessageBox.warning(self, "Missing Model", "Please load a .pkl model first.")
            return
        if not self.prediction_spectra:
            QMessageBox.warning(self, "Missing Spectra", "Please load spectra to predict.")
            return

        predictions, error = predict_from_model(self.prediction_model, self.prediction_spectra)

        if error:
            QMessageBox.critical(self, "Prediction Error", error)
            return

        self.prediction_results = predictions
        self._populate_prediction_table()
        QMessageBox.information(self, "Success", "Prediction finished successfully.")

    def _populate_prediction_table(self):
        self.prediction_table.clear()
        if not self.prediction_results:
            return

        # Get headers from the model's component list
        comp_info = self.prediction_model.get('chemical_components', [])
        headers = ["Filename"] + [f"{comp['name']} ({comp.get('unit', '')})" for comp in comp_info]
        self.prediction_table.setColumnCount(len(headers))
        self.prediction_table.setHorizontalHeaderLabels(headers)

        sorted_filenames = sorted(self.prediction_results.keys())
        self.prediction_table.setRowCount(len(sorted_filenames))

        for row, filename in enumerate(sorted_filenames):
            self.prediction_table.setItem(row, 0, QTableWidgetItem(filename))
            for col, comp in enumerate(comp_info):
                comp_name = comp['name']
                predicted_value = self.prediction_results[filename].get(comp_name, 'N/A')
                value_str = f"{predicted_value:.4f}" if isinstance(predicted_value, (int, float)) else str(predicted_value)
                self.prediction_table.setItem(row, col + 1, QTableWidgetItem(value_str))
        
        self.prediction_table.resizeColumnsToContents()
        self.prediction_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    # --- END NEW ---

    # --- NEW: Method to handle auto PLS component selection checkbox ---
    @Slot()
    def toggle_auto_pls_components(self):
        self.auto_pls_components = self.auto_pls_checkbox.isChecked()
        
        # Update the table to show/hide PLS components column
        for row in range(self.components_table.rowCount()):
            item = self.components_table.item(row, 3)  # PLS Components column
            if item:
                if self.auto_pls_components:
                    item.setText("Auto")
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make it non-editable
                else:
                    # Restore the original value from the component dictionary
                    if row < len(self.chemical_components):
                        original_value = self.chemical_components[row].get('pls_components', 10)
                        item.setText(str(original_value))
                        item.setFlags(item.flags() | Qt.ItemIsEditable)  # Make it editable
                        
        # Update the appearance of the PLS Components column
        header = self.components_table.horizontalHeader()
        if self.auto_pls_components:
            # Gray out the column header
            header.setSectionResizeMode(3, QHeaderView.Stretch)
        else:
            header.setSectionResizeMode(3, QHeaderView.Interactive)
    # --- END NEW ---

    # All component and data table update methods are unchanged
    @Slot(QTableWidgetItem)
    def update_component_value(self, item): # Unchanged
        row, col = item.row(), item.column()
        if row >= len(self.chemical_components): return
        new_value = item.text(); comp_dict = self.chemical_components[row]
        if col == 0:
            old_name = comp_dict.get('name')
            if old_name == new_value: return
            comp_dict['name'] = new_value
            if old_name in self.pls_models: self.pls_models[new_value] = self.pls_models.pop(old_name)
            if old_name in self.model_performance: self.model_performance[new_value] = self.model_performance.pop(old_name)
            for spec_data in self.spectra_data.values():
                if old_name in spec_data['refs']: spec_data['refs'][new_value] = spec_data['refs'].pop(old_name)
            self._update_all_dynamic_widgets()
        elif col == 1: comp_dict['abbrev'] = new_value
        elif col == 2: comp_dict['unit'] = new_value
        # --- NEW: Handle updates for PLS Components and CV Folds ---
        elif col in [3, 4]:
            # Skip PLS Components column if auto-selection is enabled
            if col == 3 and self.auto_pls_components:
                # Revert to "Auto" text
                self.components_table.blockSignals(True)
                item.setText("Auto")
                self.components_table.blockSignals(False)
                return
                
            try:
                val = int(new_value)
                if col == 3:
                    if val < 1: raise ValueError("Must be positive")
                    comp_dict['pls_components'] = val
                elif col == 4:
                    if val < 2: raise ValueError("Must be at least 2")
                    comp_dict['cv_folds'] = val
            except (ValueError, TypeError):
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid integer.")
                # Revert to old value
                self.components_table.blockSignals(True)
                if col == 3: item.setText(str(comp_dict.get('pls_components', 10)))
                elif col == 4: item.setText(str(comp_dict.get('cv_folds', 5)))
                self.components_table.blockSignals(False)
        # --- END NEW ---
    @Slot()
    def add_component(self): # Unchanged
        row_count = self.components_table.rowCount(); self.components_table.insertRow(row_count)
        new_comp_name = f"NewComponent{row_count+1}"
        # --- MODIFIED: Add default model parameters to the component dictionary ---
        self.chemical_components.append({
            'name': new_comp_name, 
            'abbrev': '', 
            'unit': '',
            'pls_components': 10, # Default value
            'cv_folds': 5         # Default value
        })
        # --- END MODIFIED ---
        self.components_table.blockSignals(True)
        self.components_table.setItem(row_count, 0, QTableWidgetItem(new_comp_name))
        self.components_table.setItem(row_count, 1, QTableWidgetItem(""))
        self.components_table.setItem(row_count, 2, QTableWidgetItem(""))
        # --- NEW: Set default values in the table ---
        pls_text = "Auto" if self.auto_pls_components else "10"
        pls_item = QTableWidgetItem(pls_text)
        if self.auto_pls_components:
            pls_item.setFlags(pls_item.flags() & ~Qt.ItemIsEditable)  # Make it non-editable
        self.components_table.setItem(row_count, 3, pls_item)
        self.components_table.setItem(row_count, 4, QTableWidgetItem("5"))
        # --- END NEW ---
        self.components_table.blockSignals(False); self._update_all_dynamic_widgets()
    @Slot()
    def remove_component(self): # Unchanged
        current_row = self.components_table.currentRow()
        if current_row < 0: QMessageBox.warning(self, "Warning", "Please select a component to remove."); return
        comp_name_to_remove = self.chemical_components[current_row]['name']; del self.chemical_components[current_row]
        if comp_name_to_remove in self.pls_models: del self.pls_models[comp_name_to_remove]
        if comp_name_to_remove in self.model_performance: del self.model_performance[comp_name_to_remove]
        for spec_data in self.spectra_data.values():
            if comp_name_to_remove in spec_data['refs']: del spec_data['refs'][comp_name_to_remove]
        self.components_table.removeRow(current_row); self._update_all_dynamic_widgets()
    def _update_all_dynamic_widgets(self): # Unchanged
        self.components_table.blockSignals(True)
        self.components_table.setRowCount(len(self.chemical_components))
        for i, comp in enumerate(self.chemical_components):
            self.components_table.setItem(i, 0, QTableWidgetItem(comp['name']))
            self.components_table.setItem(i, 1, QTableWidgetItem(comp.get('abbrev', '')))
            self.components_table.setItem(i, 2, QTableWidgetItem(comp.get('unit', '')))
            # --- NEW: Populate model parameter columns ---
            self.components_table.setItem(i, 3, QTableWidgetItem(str(comp.get('pls_components', 10))))
            self.components_table.setItem(i, 4, QTableWidgetItem(str(comp.get('cv_folds', 5))))
            # --- END NEW ---
        self.components_table.blockSignals(False)
        self._update_data_table_columns()
        
        # --- MODIFIED: Update component selector and performance display ---
        current_selection = self.component_selector_combo.currentText()
        self.component_selector_combo.blockSignals(True)
        self.component_selector_combo.clear()
        comp_names = [comp['name'] for comp in self.chemical_components]
        if comp_names:
            self.component_selector_combo.addItems(comp_names)
            if current_selection in comp_names:
                self.component_selector_combo.setCurrentText(current_selection)
        self.component_selector_combo.blockSignals(False)
        self.update_performance_display() # Explicitly call to refresh labels
        # --- END MODIFIED ---

    def _update_data_table_columns(self): # Unchanged
        headers = ["Filename"] + [comp['name'] for comp in self.chemical_components]
        self.data_table.setColumnCount(len(headers))
        self.data_table.setHorizontalHeaderLabels(headers)
        self.data_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._populate_data_table_rows()
    def _populate_data_table_rows(self): # Unchanged
        self.data_table.blockSignals(True); self.data_table.setRowCount(len(self.spectra_data))
        sorted_filenames = sorted(self.spectra_data.keys())
        for i, filename in enumerate(sorted_filenames):
            item_filename = QTableWidgetItem(filename); item_filename.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.data_table.setItem(i, 0, item_filename)
            for j, comp in enumerate(self.chemical_components):
                ref_value = self.spectra_data[filename]['refs'].get(comp['name'])
                val_str = f"{ref_value:.4f}" if ref_value is not None else ""
                self.data_table.setItem(i, j + 1, QTableWidgetItem(val_str))
        self.data_table.blockSignals(False)
    @Slot(QTableWidgetItem)
    def update_reference_value(self, item): # Unchanged
        col_idx = item.column();
        if col_idx == 0: return
        row_idx = item.row(); filename = self.data_table.item(row_idx, 0).text()
        comp_name = self.chemical_components[col_idx - 1]['name']
        try:
            value_str = item.text().strip(); new_value = float(value_str) if value_str else None
            self.spectra_data[filename]['refs'][comp_name] = new_value
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number.")
            old_value = self.spectra_data[filename]['refs'].get(comp_name)
            item.setText(f"{old_value:.4f}" if old_value is not None else "")

    # --- NEW: Method to update performance labels based on combobox ---
    @Slot()
    def update_performance_display(self):
        component_name = self.component_selector_combo.currentText()
        if component_name and component_name in self.model_performance:
            perf = self.model_performance[component_name]
            self.lbl_r2.setText(f"R² (CV): {perf['r2_cv']:.4f}")
            # --- NEW: Show PLS components used ---
            components_used = perf.get('pls_components', 'N/A')
            self.lbl_rmse.setText(f"RMSECV: {perf['rmsecv']:.4f} ({components_used} comp.)")
            # --- END NEW ---
        else:
            self.lbl_r2.setText("R² (CV): N/A")
            self.lbl_rmse.setText("RMSECV: N/A")
    # --- END NEW ---

    # --- NEW: Methods to handle region selection button clicks ---
    @Slot()
    def apply_region(self):
        try:
            self.region_start = float(self.start_region_input.text())
            self.region_end = float(self.end_region_input.text())
            self.plot_spectra()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numeric wavenumber values.")
            self.region_start, self.region_end = None, None

    @Slot()
    def reset_region_view(self):
        self.region_start = None
        self.region_end = None
        self.start_region_input.clear()
        self.end_region_input.clear()
        self.plot_spectra()
    # --- END NEW ---

    # --- MODIFIED: load_spectra to support both .spa and .csv files ---
    def load_spectra(self):
        """Load spectral data with user-friendly options for .spa or .csv files"""
        # Ask user what they want to do
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Load Spectral Data")
        msg_box.setText("How would you like to load your spectral data?")
        
        folder_btn = msg_box.addButton("Load .spa Folder", QMessageBox.ActionRole)
        files_btn = msg_box.addButton("Select .spa Files", QMessageBox.ActionRole)
        csv_file_btn = msg_box.addButton("Load .csv File", QMessageBox.ActionRole)
        csv_folder_btn = msg_box.addButton("Load .csv Folder", QMessageBox.ActionRole)
        cancel_btn = msg_box.addButton(QMessageBox.Cancel)

        # Set tooltips for clarity
        folder_btn.setToolTip("Load all .spa files from a folder")
        files_btn.setToolTip("Choose specific .spa files")
        csv_file_btn.setToolTip("Load spectral data from a single CSV file")
        csv_folder_btn.setToolTip("Load all CSV files from a folder")

        # Set minimum width for each button to prevent text cutoff
        min_btn_width = 240
        for btn in [folder_btn, files_btn, csv_file_btn, csv_folder_btn, cancel_btn]:
            btn.setMinimumWidth(min_btn_width)
            btn.setStyleSheet("QPushButton { font-size: 10; padding: 8px 24px; min-width: 100px; }")

        # Ensure dialog is wide and tall enough to display all buttons without clipping
        msg_box.setStyleSheet("QMessageBox { min-width: 1050px; min-height: 220px; }")

        msg_box.exec_()
        
        if msg_box.clickedButton() == cancel_btn:
            return
        elif msg_box.clickedButton() == folder_btn:
            # Original folder selection logic
            folder_path = QFileDialog.getExistingDirectory(self, "Select Folder Containing .spa Files")
            if not folder_path: 
                return
            
            self.current_folder_path = folder_path  # Store for reference
            self.spectra_data, self.wavenumbers = load_spectra_from_folder(folder_path)
            
            if not self.spectra_data:
                QMessageBox.warning(self, "No Files Found", "No .spa files found in the selected folder.")
                return
                
            self._update_all_dynamic_widgets()
            self.reset_plot()
            QMessageBox.information(self, "Success", f"Loaded {len(self.spectra_data)} spectra from folder.")
            
        elif msg_box.clickedButton() == files_btn:
            # Individual .spa file selection logic
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, 
                "Select .spa Files", 
                "", 
                "SPA Files (*.spa);;All Files (*)"
            )
            
            if not file_paths:
                return
            
            # Store folder path of the first file for reference
            if file_paths:
                self.current_folder_path = os.path.dirname(file_paths[0])
            
            from logic.processing import load_selected_spa_files
            self.spectra_data, self.wavenumbers = load_selected_spa_files(file_paths)
            
            if not self.spectra_data:
                QMessageBox.warning(self, "No Files Loaded", "Could not load any of the selected files.")
                return
                
            self._update_all_dynamic_widgets()
            self.reset_plot()
            
            # Show summary of what was loaded
            summary = f"Loaded {len(self.spectra_data)} spectra from {len(file_paths)} selected files."
            if len(self.spectra_data) < len(file_paths):
                failed_count = len(file_paths) - len(self.spectra_data)
                summary += f"\n{failed_count} files failed to load."
            QMessageBox.information(self, "Success", summary)
            
        elif msg_box.clickedButton() == csv_file_btn:
            # CSV file selection logic
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Select CSV File with Spectral Data", 
                "", 
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if not file_path:
                return
            
            # Store folder path for reference
            self.current_folder_path = os.path.dirname(file_path)
            
            from logic.processing import load_csv_spectral_data
            result = load_csv_spectral_data(file_path)
            
            if result[0] is None:
                QMessageBox.critical(self, "Error", f"Failed to load CSV file:\n{result[1]}")
                return
                
            self.spectra_data, self.wavenumbers = result
            self._update_all_dynamic_widgets()
            self.reset_plot()
            
            QMessageBox.information(self, "Success", f"Loaded {len(self.spectra_data)} spectra from CSV file.")
            
        elif msg_box.clickedButton() == csv_folder_btn:
            # CSV folder selection logic
            folder_path = QFileDialog.getExistingDirectory(self, "Select Folder Containing CSV Files")
            if not folder_path:
                return
            
            # Store folder path for reference
            self.current_folder_path = folder_path
            
            from logic.processing import load_csv_folder_spectral_data
            result = load_csv_folder_spectral_data(folder_path)
            
            if result[0] is None:
                QMessageBox.critical(self, "Error", f"Failed to load CSV files from folder:\n{result[1]}")
                return
                
            self.spectra_data, self.wavenumbers = result
            self._update_all_dynamic_widgets()
            self.reset_plot()
            
            QMessageBox.information(self, "Success", f"Loaded {len(self.spectra_data)} spectra from {folder_path}.")
    
    # --- MODIFIED: Rename method comment for clarity ---

    # --- MODIFIED: train_pls_model_action to loop through all components ---
    def train_pls_model_action(self):
        if not self.chemical_components:
            QMessageBox.warning(self, "Warning", "Please define at least one component in the 'Components' tab before training.")
            return
        
        if not self.spectra_data:
            QMessageBox.warning(self, "Warning", "Please load spectral data before training.")
            return

        self.pls_models.clear()
        self.model_performance.clear()
        
        success_count = 0
        error_messages = []

        for component in self.chemical_components:
            target_component = component['name']
            cv_folds = component['cv_folds']
            
            # --- NEW: Handle auto PLS component selection ---
            if self.auto_pls_components:
                # Find optimal number of components
                optimal_components, best_r2, auto_error = find_optimal_pls_components(
                    self.spectra_data,
                    target_component,
                    self.current_derivative,
                    self.wavenumbers,
                    self.region_start,
                    self.region_end,
                    cv_folds
                )
                
                if auto_error:
                    error_messages.append(f"Could not find optimal components for '{target_component}':\n{auto_error}")
                    continue
                    
                num_components = optimal_components
                # Update the component dictionary with the found optimal value
                component['pls_components'] = num_components
            else:
                num_components = component['pls_components']
            # --- END NEW ---

            model, scaler, r2_cv, rmsecv, error = train_pls_model(
                self.spectra_data,
                target_component,
                num_components,
                self.current_derivative,
                self.wavenumbers,
                self.region_start,
                self.region_end,
                cv_folds
            )

            if error:
                error_messages.append(f"Could not train model for '{target_component}':\n{error}")
            else:
                self.pls_models[target_component] = {'model': model, 'scaler': scaler}
                # --- NEW: Store the number of components used for display ---
                self.model_performance[target_component] = {
                    'r2_cv': r2_cv, 
                    'rmsecv': rmsecv,
                    'pls_components': num_components
                }
                # --- END NEW ---
                success_count += 1
        
        # --- Report summary of training ---
        summary_message = f"Training finished for {len(self.chemical_components)} component(s).\n\n"
        summary_message += f"Successfully trained: {success_count}\n"
        summary_message += f"Failed: {len(error_messages)}\n\n"
        
        # --- NEW: Add info about auto-selection ---
        if self.auto_pls_components:
            summary_message += "Auto-selection of PLS components was used.\n"
            if success_count > 0:
                summary_message += "Check the performance display to see the optimal number of components found for each model."
        # --- END NEW ---

        # --- MODIFIED: Use a custom resizable dialog for showing details ---
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Training Report")
        msg_box.setText(summary_message)
        msg_box.setStandardButtons(QMessageBox.Ok)

        if error_messages:
            detailed_text = "--- Errors ---\n" + "\n\n".join(error_messages)
            msg_box.setDetailedText(detailed_text)
            msg_box.setIcon(QMessageBox.Warning)
            # Find the text edit for detailed text and make it readable
            # This is a bit of a hack, but it's a common way to customize QMessageBox
            for child in msg_box.findChildren(QTextEdit):
                child.setReadOnly(True) # Ensure it's not editable
                child.setStyleSheet("QTextEdit { background-color: #FFFFFF; color: #000000; }")
                break # Stop after finding the first one
        else:
            msg_box.setIcon(QMessageBox.Information)

        # Make the message box resizable by accessing its layout
        # This is another hacky but effective approach
        sp = msg_box.findChild(QSplitter)
        if sp:
            sp.setHandleWidth(1) # Make the splitter handle visible and draggable
        
        # A more robust way to make it resizable
        msg_box.setSizeGripEnabled(True)
        msg_box.setStyleSheet("QMessageBox { min-width: 400px; min-height: 200px; }")


        msg_box.exec()
        # --- END MODIFIED ---

        # Refresh the performance display for the currently selected component
        self.update_performance_display()

    # --- NEW: Complete Project Save/Load Methods ---
    @Slot()
    def save_complete_project(self):
        """Save complete project including spectral data, models, and all settings"""
        if not self.spectra_data:
            QMessageBox.warning(self, "Warning", "No spectral data loaded. Please load spectra first.")
            return
        
        # Propose a filename based on the first component, for convenience
        first_comp = self.chemical_components[0]['name'] if self.chemical_components else "project"
        default_filename = f"{first_comp.replace(' ', '_')}_complete_project.irs"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Complete Project", default_filename,
            "IRIS Project (*.irs);;Legacy Pickle (*.pkl);;All Files (*)"
        )
        
        if not file_path:
            return
        
        success, message = save_complete_project(
            self.spectra_data, self.chemical_components, self.pls_models, 
            self.model_performance, self.wavenumbers, self.current_derivative,
            self.region_start, self.region_end, self.auto_pls_components, file_path
        )
        
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)
    
    @Slot()
    def load_complete_project(self):
        """Load complete project including spectral data, models, and all settings"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Complete Project", "",
            "IRIS Project (*.irs);;Legacy Pickle (*.pkl);;All Files (*)"
        )
        
        if not file_path:
            return
        
        project_data, message = load_complete_project(file_path)
        
        if project_data is None:
            QMessageBox.critical(self, "Error", message)
            return
        
        # Ask user for confirmation as this will replace current data
        reply = QMessageBox.question(
            self, "Load Complete Project",
            f"{message}\n\nThis will replace all current data. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            # Restore all project data
            self.chemical_components = project_data.get('chemical_components', [])
            self.pls_models = project_data.get('pls_models', {})
            self.model_performance = project_data.get('model_performance', {})
            self.wavenumbers = project_data.get('wavenumbers', None)
            self.current_derivative = project_data.get('current_derivative', 0)
            self.region_start = project_data.get('region_start', None)
            self.region_end = project_data.get('region_end', None)
            
            # Reconstruct spectra data
            spectral_data = project_data.get('spectral_data', {})
            reference_values = project_data.get('reference_values', {})
            
            if spectral_data and self.wavenumbers is not None:
                self.spectra_data = reconstruct_spectra_data(spectral_data, reference_values, self.wavenumbers)
            else:
                self.spectra_data = {}
            
            # Update auto PLS setting and refresh component table
            self.auto_pls_components = project_data.get('auto_pls_components', False)
            self.auto_pls_checkbox.setChecked(self.auto_pls_components)
            
            # Update all UI elements to restore exact appearance
            self._update_all_dynamic_widgets()
            self._update_derivative_display()
            self._update_region_display()
            
            # Ensure the component table reflects the auto PLS setting
            self.toggle_auto_pls_components()
            
            # Plot with loaded settings to restore the exact view
            self.plot_spectra()
            
            QMessageBox.information(self, "Success", "Complete project loaded successfully!")
    
    
    # --- NEW: Export model for prediction method ---
    @Slot()
    def export_model_for_prediction(self):
        """Export trained models for use in prediction"""
        if not self.pls_models:
            QMessageBox.warning(self, "Warning", "No trained models available. Please train models first.")
            return
        
        if not self.chemical_components:
            QMessageBox.warning(self, "Warning", "No component definitions available.")
            return
        
        # Propose a filename based on the first component, for convenience
        first_comp = self.chemical_components[0]['name'] if self.chemical_components else "model"
        default_filename = f"{first_comp.replace(' ', '_')}_prediction_model.pkl"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Model for Prediction", default_filename,
            "Pickle Model (*.pkl);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Create the prediction model data structure
            prediction_model_data = {
                'project_type': 'prediction_model',
                'chemical_components': self.chemical_components,
                'pls_models': self.pls_models,
                'model_performance': self.model_performance,
                'wavenumbers': self.wavenumbers.tolist() if self.wavenumbers is not None else None,
                'processing_settings': {
                    'derivative_order': self.current_derivative,
                    'region_start': self.region_start,
                    'region_end': self.region_end
                },
                'export_timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            # Save using joblib for compatibility
            with open(file_path, 'wb') as f:
                joblib.dump(prediction_model_data, f)
            
            stats = {
                'models': len(self.pls_models),
                'components': len(self.chemical_components)
            }
            
            message = (f"Model exported successfully for prediction!\n"
                      f"• {stats['models']} trained models\n"
                      f"• {stats['components']} components\n"
                      f"• Processing settings included\n"
                      f"• Exported to: {file_path}")
            
            QMessageBox.information(self, "Success", message)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export model: {str(e)}")
    # --- END NEW ---

    # Helper methods for UI updates
    def _update_derivative_display(self):
        """Update UI to reflect current derivative setting"""
        self.btn_original.setChecked(self.current_derivative == 0)
        self.btn_deriv1.setChecked(self.current_derivative == 1)
        self.btn_deriv2.setChecked(self.current_derivative == 2)
    
    def _update_region_display(self):
        """Update region input fields"""
        self.start_region_input.setText(str(self.region_start) if self.region_start is not None else "")
        self.end_region_input.setText(str(self.region_end) if self.region_end is not None else "")
    
    # --- END NEW ---

    def _style_matplotlib_toolbar(self): # Enhanced to fix coordinate display
        # Style the toolbar icons
        icon_color = QColor(UP_DARK_GRAY)
        for action in self.toolbar.actions():
            if action.icon() and not action.icon().isNull():
                pixmap = action.icon().pixmap(32, 32); painter = QPainter(pixmap)
                painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
                painter.fillRect(pixmap.rect(), icon_color); painter.end()
                action.setIcon(QIcon(pixmap))
        
        # Style the toolbar's coordinate display label to ensure readable text
        self.toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {UP_LIGHT_GRAY};
                color: {UP_DARK_GRAY};
                border: none;
            }}
            QLabel {{
                color: {UP_DARK_GRAY};
                background-color: {UP_LIGHT_GRAY};
                padding: 2px 4px;
                border-radius: 3px;
                font-weight: bold;
            }}
        """)

    def apply_derivative(self, deriv_order):
        self.current_derivative = deriv_order
        self._update_derivative_display()
        self.plot_spectra()

    # --- MODIFIED: plot_spectra to apply the visual zoom ---
    def plot_spectra(self):
        self.ax.clear()
        if not self.spectra_data:
            self.ax.text(0.5, 0.5, 'No data loaded', ha='center'); self.canvas.draw()
            return
            
        for filename, data in self.spectra_data.items():
            processed_intensity = get_processed_intensity(data['intensity'], self.current_derivative)
            self.ax.plot(data['nd'].x.data, processed_intensity, label=filename)
            
        title = "Original Spectra"
        if self.current_derivative == 1: title = "1st Derivative"
        elif self.current_derivative == 2: title = "2nd Derivative"
            
        self.ax.set_title(f"Spectra Viewer: {title}", fontsize=16, color=UP_MAROON, weight='bold')
        self.ax.set_xlabel('Wavenumber (cm⁻¹)'); self.ax.set_ylabel('Absorbance / Intensity')
        self.ax.invert_xaxis()

        # --- NEW: Set x-axis limits based on the selected region ---
        if self.region_start is not None and self.region_end is not None:
            self.ax.set_xlim(max(self.region_start, self.region_end), 
                             min(self.region_start, self.region_end))
        else:
            if self.wavenumbers is not None:
                self.ax.set_xlim(self.wavenumbers.max(), self.wavenumbers.min())
        # --- END NEW ---

        self.ax.set_facecolor(UP_WHITE); self.ax.grid(True, linestyle='--', color=UP_DARK_GRAY, alpha=0.3)
        self.ax.tick_params(colors=UP_DARK_GRAY)
        for spine in self.ax.spines.values(): spine.set_edgecolor(UP_DARK_GRAY)
            
        if len(self.spectra_data) <= 20 and self.legend_visible:
            self.ax.legend(fontsize='small')
            
        self.fig.tight_layout(); self.canvas.draw()

    # --- MODIFIED: reset_plot should also reset the region view ---
    def reset_plot(self):
        self.current_derivative = 0
        self._update_derivative_display()
        self.reset_region_view() # This now handles resetting the zoom and replotting

    def toggle_legend(self): # Unchanged
        self.legend_visible = not self.legend_visible
        self.plot_spectra()

    # --- NEW: CSV Import/Export Methods ---
    @Slot()
    def import_calibration_csv(self):
        """Import calibration data reference values from CSV"""
        if not self.spectra_data:
            QMessageBox.warning(self, "Warning", "No spectral data loaded. Please load spectra first.")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Calibration Data from CSV", "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                headers = next(reader)
                
                # Extract filename column and component columns
                if not headers or headers[0].lower() != 'filename':
                    QMessageBox.warning(self, "Import Error", "CSV file must have 'Filename' as the first column.")
                    return
                
                component_headers = headers[1:]
                
                # Ask user if they want to update existing components or create new ones
                reply = QMessageBox.question(
                    self, "Import Components",
                    f"Found {len(component_headers)} components in CSV:\n{', '.join(component_headers[:3])}{'...' if len(component_headers) > 3 else ''}\n\nCreate/update components from CSV?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # Update or create components
                    for header in component_headers:
                        # Remove unit from header if present (e.g., "Protein (%)" -> "Protein")
                        comp_name = header.split('(')[0].strip()
                        unit = ""
                        if '(' in header and ')' in header:
                            unit = header.split('(')[1].split(')')[0].strip()
                        
                        # Check if component exists
                        existing_comp = next((comp for comp in self.chemical_components if comp['name'] == comp_name), None)
                        if not existing_comp:
                            # Create new component
                            new_component = {
                                'name': comp_name,
                                'abbreviation': comp_name[:3].upper(),
                                'unit': unit,
                                'pls_components': 10,
                                'cv_folds': 5
                            }
                            self.chemical_components.append(new_component)
                
                # Read data rows
                imported_count = 0
                updated_count = 0
                missing_spectra = []
                
                for row in reader:
                    if not row:
                        continue
                    
                    filename = row[0]
                    if filename in self.spectra_data:
                        # Update reference values
                        for i, value_str in enumerate(row[1:]):
                            if i < len(component_headers) and value_str.strip():
                                try:
                                    value = float(value_str)
                                    comp_name = component_headers[i].split('(')[0].strip()
                                    self.spectra_data[filename]['refs'][comp_name] = value
                                    updated_count += 1
                                except ValueError:
                                    continue
                        imported_count += 1
                    else:
                        missing_spectra.append(filename)
                
                # Update UI
                self._update_all_dynamic_widgets()
                
                # Show summary
                summary = f"CSV import completed!\n\n"
                summary += f"• {imported_count} spectra updated\n"
                summary += f"• {updated_count} reference values imported\n"
                summary += f"• {len(self.chemical_components)} components total\n"
                
                if missing_spectra:
                    summary += f"• {len(missing_spectra)} spectra not found in current data"
                    if len(missing_spectra) <= 5:
                        summary += f"\n  Missing: {', '.join(missing_spectra)}"
                
                QMessageBox.information(self, "Import Successful", summary)
                
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import calibration data: {str(e)}")

    @Slot()
    def export_calibration_csv(self):
        """Export calibration data reference values to CSV"""
        if not self.spectra_data:
            QMessageBox.warning(self, "Warning", "No spectral data loaded. Please load spectra first.")
            return
        
        # Check if there are any reference values to export
        has_refs = any(data['refs'] for data in self.spectra_data.values())
        if not has_refs:
            QMessageBox.warning(self, "Warning", "No reference values entered. Please enter some reference values first.")
            return
        
        # Propose a filename
        first_comp = self.chemical_components[0]['name'] if self.chemical_components else "calibration"
        default_filename = f"{first_comp.replace(' ', '_')}_calibration_data.csv"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Calibration Data to CSV", default_filename,
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                header = ['Filename']
                for comp in self.chemical_components:
                    unit_str = f" ({comp['unit']})" if comp.get('unit') else ""
                    header.append(f"{comp['name']}{unit_str}")
                writer.writerow(header)
                
                # Write data rows
                sorted_filenames = sorted(self.spectra_data.keys())
                for filename in sorted_filenames:
                    row = [filename]
                    for comp in self.chemical_components:
                        ref_value = self.spectra_data[filename]['refs'].get(comp['name'])
                        if ref_value is not None:
                            row.append(f"{ref_value:.4f}")
                        else:
                            row.append("")
                    writer.writerow(row)
            
            # Count statistics
            total_spectra = len(self.spectra_data)
            spectra_with_refs = sum(1 for data in self.spectra_data.values() if data['refs'])
            total_values = sum(len([v for v in data['refs'].values() if v is not None]) 
                             for data in self.spectra_data.values())
            
            QMessageBox.information(
                self, "Export Successful", 
                f"Calibration data exported successfully!\n\n"
                f"• {total_spectra} spectra\n"
                f"• {spectra_with_refs} spectra with reference values\n"
                f"• {total_values} reference values\n"
                f"• {len(self.chemical_components)} components\n"
                f"• Saved to: {file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export calibration data: {str(e)}")

    @Slot()
    def export_prediction_csv(self):
        """Export prediction results to CSV"""
        if not self.prediction_results:
            QMessageBox.warning(self, "Warning", "No prediction results available. Please run prediction first.")
            return
        
        # Get component info from the loaded model
        if not self.prediction_model:
            QMessageBox.warning(self, "Warning", "No prediction model loaded.")
            return
        
        comp_info = self.prediction_model.get('chemical_components', [])
        
        # Propose a filename
        default_filename = "prediction_results.csv"
        if comp_info:
            first_comp = comp_info[0]['name']
            default_filename = f"{first_comp.replace(' ', '_')}_prediction_results.csv"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Prediction Results to CSV", default_filename,
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                header = ['Filename']
                for comp in comp_info:
                    unit_str = f" ({comp['unit']})" if comp.get('unit') else ""
                    header.append(f"{comp['name']}{unit_str}")
                writer.writerow(header)
                
                # Write data rows
                sorted_filenames = sorted(self.prediction_results.keys())
                for filename in sorted_filenames:
                    row = [filename]
                    for comp in comp_info:
                        comp_name = comp['name']
                        predicted_value = self.prediction_results[filename].get(comp_name, 'N/A')
                        if isinstance(predicted_value, (int, float)):
                            row.append(f"{predicted_value:.4f}")
                        else:
                            row.append(str(predicted_value))
                    writer.writerow(row)
            
            # Count statistics
            total_spectra = len(self.prediction_results)
            total_predictions = sum(len(results) for results in self.prediction_results.values())
            
            QMessageBox.information(
                self, "Export Successful", 
                f"Prediction results exported successfully!\n\n"
                f"• {total_spectra} spectra\n"
                f"• {total_predictions} predictions\n"
                f"• {len(comp_info)} components\n"
                f"• Saved to: {file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export prediction results: {str(e)}")

    # --- NEW: Spectral Data Import/Export Methods ---
    @Slot()
    def export_spa_individual_csv(self):
        """Export each loaded SPA file to individual CSV files"""
        if not self.spectra_data:
            QMessageBox.warning(self, "Warning", "No spectral data loaded. Please load SPA files first.")
            return
        
        output_folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder for Individual CSV Files"
        )
        
        if not output_folder:
            return
        
        success_count, error_messages = export_spa_to_csv_individual(
            self.spectra_data, 
            self.wavenumbers, 
            output_folder, 
            self.current_derivative
        )
        
        # Show results
        derivative_info = ""
        if self.current_derivative == 1:
            derivative_info = " (1st derivative applied)"
        elif self.current_derivative == 2:
            derivative_info = " (2nd derivative applied)"
        
        if error_messages:
            detailed_text = "\n".join(error_messages)
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Export Results")
            msg_box.setText(f"Export completed with some errors.\n\nSuccessfully exported: {success_count} files{derivative_info}")
            msg_box.setDetailedText(detailed_text)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.exec()
        else:
            QMessageBox.information(
                self, "Export Successful", 
                f"Successfully exported {success_count} SPA files to individual CSV files{derivative_info}!\n\n"
                f"Output folder: {output_folder}\n"
                f"Files created: {success_count}"
            )

    @Slot()
    def export_spa_combined_csv(self):
        """Export all loaded SPA files to a single combined CSV file"""
        if not self.spectra_data:
            QMessageBox.warning(self, "Warning", "No spectral data loaded. Please load SPA files first.")
            return
        
        # Propose filename based on current settings
        derivative_suffix = ""
        if self.current_derivative == 1:
            derivative_suffix = "_1st_derivative"
        elif self.current_derivative == 2:
            derivative_suffix = "_2nd_derivative"
        
        default_filename = f"combined_spectra{derivative_suffix}.csv"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Combined CSV File", default_filename,
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        success, error_message = export_spa_to_csv_combined(
            self.spectra_data,
            self.wavenumbers,
            file_path,
            self.current_derivative
        )
        
        if success:
            derivative_info = ""
            if self.current_derivative == 1:
                derivative_info = " (1st derivative applied)"
            elif self.current_derivative == 2:
                derivative_info = " (2nd derivative applied)"
            
            QMessageBox.information(
                self, "Export Successful",
                f"Successfully exported {len(self.spectra_data)} SPA files to combined CSV{derivative_info}!\n\n"
                f"File: {file_path}\n"
                f"Columns: Wavenumber + {len(self.spectra_data)} spectra\n"
                f"Data points: {len(self.wavenumbers)}"
            )
        else:
            QMessageBox.critical(self, "Export Error", f"Failed to export combined CSV: {error_message}")
    # --- END NEW ---