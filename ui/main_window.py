import sys
import os
import joblib
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog,
    QSplitter, QGridLayout, QLabel, QHeaderView, QMessageBox,
    QSpinBox, QTabWidget, QComboBox, QLineEdit, QTextEdit
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QTextOption

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

# Import from the correct, separated logic and ui files
from logic.processing import load_spectra_from_folder, train_pls_model, get_processed_intensity
from .stylesheet import UP_MAROON, UP_FOREST_GREEN, UP_WHITE, UP_LIGHT_GRAY, UP_DARK_GRAY

class SpectraViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive Chemometrics App - UPLB-IPB")
        self.setGeometry(100, 100, 1600, 900)

        self.spectra_data = {}
        self.chemical_components = []
        self.pls_models = {}
        self.current_derivative = 0
        self.legend_visible = True

        # --- NEW: State variables for model performance ---
        self.model_performance = {} # Stores {comp_name: {'r2_cv': 0.99, 'rmsecv': 0.1}}
        # --- END NEW ---

        # --- NEW: State variables for region selection ---
        self.wavenumbers = None
        self.region_start = None
        self.region_end = None
        # --- END NEW ---

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.calibration_tab = self._create_calibration_tab()
        self.components_tab = self._create_components_tab()
        self.tabs.addTab(self.calibration_tab, "Calibration")
        self.tabs.addTab(self.components_tab, "Components")

        # --- NEW: Connect component selector change to performance display update ---
        self.component_selector_combo.currentIndexChanged.connect(self.update_performance_display)
        # --- END NEW ---

    def _create_components_tab(self):
        # This method is unchanged
        container = QWidget()
        layout = QVBoxLayout(container); layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel("Define Chemical Components & Model Parameters"); title.setObjectName("TabTitle") # Changed Title
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
        layout.addWidget(title); layout.addWidget(self.components_table); layout.addLayout(btn_layout); layout.addStretch()
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
        lp_layout = QVBoxLayout(left_panel); lp_layout.setContentsMargins(15, 15, 15, 15); lp_layout.setSpacing(10)
        
        # --- MODIFIED: Simplified Training Controls ---
        train_layout = QGridLayout(); train_layout.setSpacing(8)
        self.btn_load_folder = QPushButton("1. Load .spa Files")
        lbl_step2 = QLabel("2. Enter Reference Values in Table"); lbl_step2.setObjectName("PerfLabel")
        lbl_step3 = QLabel("3. Define Components in 'Components' Tab"); lbl_step3.setObjectName("PerfLabel")
        self.btn_train_pls = QPushButton("4. Train All Models") # Changed text and step number

        train_layout.addWidget(self.btn_load_folder, 0, 0, 1, 2)
        train_layout.addWidget(lbl_step2, 1, 0, 1, 2)
        train_layout.addWidget(lbl_step3, 2, 0, 1, 2)
        train_layout.addWidget(self.btn_train_pls, 3, 0, 1, 2) # Moved to row 3
        # --- END MODIFIED ---

        # --- NEW: Import/Export Controls ---
        io_header_label = QLabel("Model Management"); io_header_label.setObjectName("PanelHeaderLabel")
        io_layout = QGridLayout(); io_layout.setSpacing(8)
        self.btn_import_models = QPushButton("Import Models")
        self.btn_export_models = QPushButton("Export Models")
        io_layout.addWidget(self.btn_import_models, 0, 0)
        io_layout.addWidget(self.btn_export_models, 0, 1)
        # --- END NEW ---

        # --- Region Selection / Zoom Controls (Unchanged) ---
        region_header_label = QLabel("Region Selection / Zoom"); region_header_label.setObjectName("PanelHeaderLabel")
        region_layout = QGridLayout(); region_layout.setSpacing(8)
        
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

        table_header_label = QLabel("Calibration Data"); table_header_label.setObjectName("PanelHeaderLabel")
        self.data_table = QTableWidget(); self.data_table.itemChanged.connect(self.update_reference_value)

        # --- MODIFIED: Performance display now linked to the component selector ---
        perf_label = QLabel("Model Performance"); perf_label.setObjectName("PanelHeaderLabel")
        perf_layout = QGridLayout()
        # Add the component selector here to choose which model's performance to view
        lbl_perf_comp = QLabel("Show Performance For:"); lbl_perf_comp.setObjectName("PerfLabel")
        self.component_selector_combo = QComboBox(); self.component_selector_combo.setObjectName("ComboBox")
        self.lbl_r2, self.lbl_rmse = QLabel("R² (CV): N/A"), QLabel("RMSECV: N/A")
        self.lbl_r2.setObjectName("PerfLabel"); self.lbl_rmse.setObjectName("PerfLabel")
        perf_layout.addWidget(lbl_perf_comp, 0, 0)
        perf_layout.addWidget(self.component_selector_combo, 0, 1)
        perf_layout.addWidget(self.lbl_r2, 1, 0)
        perf_layout.addWidget(self.lbl_rmse, 1, 1)
        # --- END MODIFIED ---
        
        # --- MODIFIED: Assemble the left panel with the new section ---
        lp_layout.addLayout(train_layout)
        lp_layout.addWidget(io_header_label)
        lp_layout.addLayout(io_layout)
        lp_layout.addWidget(region_header_label)
        lp_layout.addLayout(region_layout)
        lp_layout.addWidget(table_header_label)
        lp_layout.addWidget(self.data_table)
        lp_layout.addWidget(perf_label)
        lp_layout.addLayout(perf_layout)

        # --- MODIFIED: Connect all button signals ---
        self.btn_load_folder.clicked.connect(self.load_folder)
        self.btn_train_pls.clicked.connect(self.train_pls_model_action)
        self.btn_import_models.clicked.connect(self.import_models)
        self.btn_export_models.clicked.connect(self.export_models)
        self.btn_apply_region.clicked.connect(self.apply_region)
        self.btn_reset_region.clicked.connect(self.reset_region_view)
        
        right_panel = self._create_plot_panel()
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setStretchFactor(0, 1); main_splitter.setStretchFactor(1, 2)
        return main_widget

    def _create_plot_panel(self):
        # This method is unchanged
        container, layout = QWidget(), QVBoxLayout()
        self.fig = Figure(figsize=(10, 7), dpi=100, facecolor=UP_LIGHT_GRAY)
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.btn_plot = QPushButton("Plot Spectra"); self.btn_reset = QPushButton("Reset Plot")
        self.btn_deriv1 = QPushButton("1st Derivative"); self.btn_deriv2 = QPushButton("2nd Derivative")
        plot_btn_layout = QHBoxLayout()
        plot_btn_layout.addWidget(self.btn_plot); plot_btn_layout.addWidget(self.btn_reset)
        plot_btn_layout.addWidget(self.btn_deriv1); plot_btn_layout.addWidget(self.btn_deriv2)
        self.btn_plot.clicked.connect(self.plot_spectra); self.btn_reset.clicked.connect(self.reset_plot)
        self.btn_deriv1.clicked.connect(lambda: self.apply_derivative(1)); self.btn_deriv2.clicked.connect(lambda: self.apply_derivative(2))
        self.toolbar = NavigationToolbar(self.canvas, self)
        self._style_matplotlib_toolbar()
        layout.addLayout(plot_btn_layout); layout.addWidget(self.toolbar); layout.addWidget(self.canvas)
        container.setLayout(layout)
        self.reset_plot()
        return container

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
        self.components_table.setItem(row_count, 3, QTableWidgetItem("10"))
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
            self.lbl_rmse.setText(f"RMSECV: {perf['rmsecv']:.4f}")
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

    # --- MODIFIED: load_folder to capture wavenumbers from the logic function ---
    def load_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder Containing .spa Files")
        if not folder_path: return
        self.spectra_data, self.wavenumbers = load_spectra_from_folder(folder_path)
        self._update_all_dynamic_widgets()
        self.reset_plot() # This will now reset the region view and plot
        QMessageBox.information(self, "Success", f"Loaded {len(self.spectra_data)} spectra.")

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
            num_components = component['pls_components']
            cv_folds = component['cv_folds']

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
                self.model_performance[target_component] = {'r2_cv': r2_cv, 'rmsecv': rmsecv}
                success_count += 1
        
        # --- Report summary of training ---
        summary_message = f"Training finished for {len(self.chemical_components)} component(s).\n\n"
        summary_message += f"Successfully trained: {success_count}\n"
        summary_message += f"Failed: {len(error_messages)}"

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

    # --- NEW: Import/Export Methods ---
    @Slot()
    def export_models(self):
        if not self.pls_models:
            QMessageBox.warning(self, "No Models to Export", "Please train at least one model before exporting.")
            return

        # Propose a filename based on the first component, for convenience
        first_comp = self.chemical_components[0]['name'] if self.chemical_components else "model"
        default_filename = f"{first_comp.replace(' ', '_')}_models.chemom"

        filePath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Models",
            default_filename,
            "Chemometrics Models (*.chemom);;All Files (*)"
        )

        if not filePath:
            return

        # Consolidate all relevant data into a single dictionary
        export_data = {
            'pls_models': self.pls_models,
            'chemical_components': self.chemical_components,
            'model_performance': self.model_performance,
            'wavenumbers': self.wavenumbers,
            'processing_settings': {
                'derivative_order': self.current_derivative,
                'region_start': self.region_start,
                'region_end': self.region_end,
            }
        }

        try:
            joblib.dump(export_data, filePath)
            QMessageBox.information(self, "Success", f"Models successfully exported to:\n{filePath}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"An error occurred while exporting the models:\n{e}")

    @Slot()
    def import_models(self):
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Models",
            "",
            "Chemometrics Models (*.chemom);;All Files (*)"
        )

        if not filePath:
            return

        try:
            imported_data = joblib.load(filePath)

            # --- Data Validation ---
            required_keys = ['pls_models', 'chemical_components', 'model_performance', 'wavenumbers']
            if not all(key in imported_data for key in required_keys):
                raise ValueError("The imported file is missing required data structures.")

            # --- State Restoration ---
            self.pls_models = imported_data.get('pls_models', {})
            self.chemical_components = imported_data.get('chemical_components', [])
            self.model_performance = imported_data.get('model_performance', {})
            self.wavenumbers = imported_data.get('wavenumbers', None)
            
            # Restore processing settings if they exist in the file
            proc_settings = imported_data.get('processing_settings', {})
            self.current_derivative = proc_settings.get('derivative_order', 0)
            self.region_start = proc_settings.get('region_start', None)
            self.region_end = proc_settings.get('region_end', None)

            # --- UI Refresh ---
            # Clear existing data from tables and plots
            self.spectra_data.clear() # Clear any loaded spectra, as they are not part of the model file
            self.data_table.setRowCount(0)
            self.reset_plot()

            # Update all UI elements with the new state
            self._update_all_dynamic_widgets()
            
            # Update region inputs
            self.start_region_input.setText(str(self.region_start) if self.region_start is not None else "")
            self.end_region_input.setText(str(self.region_end) if self.region_end is not None else "")

            QMessageBox.information(self, "Success", "Models and settings have been successfully imported.")

        except FileNotFoundError:
            QMessageBox.critical(self, "Import Error", "The selected file could not be found.")
        except ValueError as ve:
             QMessageBox.critical(self, "Import Error", f"Invalid file format: {ve}")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"An unexpected error occurred while importing the models:\n{e}")
    # --- END NEW ---

    def _style_matplotlib_toolbar(self): # Unchanged
        icon_color = QColor(UP_DARK_GRAY)
        for action in self.toolbar.actions():
            if action.icon() and not action.icon().isNull():
                pixmap = action.icon().pixmap(32, 32); painter = QPainter(pixmap)
                painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
                painter.fillRect(pixmap.rect(), icon_color); painter.end()
                action.setIcon(QIcon(pixmap))

    def apply_derivative(self, deriv_order): # Unchanged
        self.current_derivative = deriv_order
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
        self.reset_region_view() # This now handles resetting the zoom and replotting

    def toggle_legend(self): # Unchanged
        self.legend_visible = not self.legend_visible
        self.plot_spectra()