
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog,
    QSplitter, QGridLayout, QLabel, QHeaderView, QMessageBox,
    QSpinBox, QTabWidget, QComboBox
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

from logic.processing import load_spectra_from_folder, train_pls_model, get_processed_intensity
from .stylesheet import STYLESHEET, UP_MAROON, UP_FOREST_GREEN, UP_GOLD, UP_WHITE, UP_LIGHT_GRAY, UP_DARK_GRAY, UP_MEDIUM_GRAY

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

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.calibration_tab = self._create_calibration_tab()
        self.components_tab = self._create_components_tab()
        self.tabs.addTab(self.calibration_tab, "Calibration")
        self.tabs.addTab(self.components_tab, "Components")

    def _create_components_tab(self):
        container = QWidget()
        layout = QVBoxLayout(container); layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel("Define Chemical Components"); title.setObjectName("TabTitle")
        self.components_table = QTableWidget()
        self.components_table.setColumnCount(3); self.components_table.setHorizontalHeaderLabels(["Component Name", "Abbreviation", "Unit"])
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

        left_panel = QWidget()
        left_panel.setObjectName("ControlPanel")
        lp_layout = QVBoxLayout(left_panel)
        lp_layout.setContentsMargins(15, 15, 15, 15); lp_layout.setSpacing(10)
        
        train_layout = QGridLayout(); train_layout.setSpacing(8)
        self.btn_load_folder = QPushButton("1. Load .spa Files")
        
        lbl_step2 = QLabel("2. Enter Reference Values in Table"); lbl_step2.setObjectName("PerfLabel")
        lbl_step3 = QLabel("3. Select Component to Model:"); lbl_step3.setObjectName("PerfLabel")
        self.component_selector_combo = QComboBox(); self.component_selector_combo.setObjectName("ComboBox")
        lbl_step4 = QLabel("4. Set PLS Components:"); lbl_step4.setObjectName("PerfLabel")
        self.pls_components_spinbox = QSpinBox()
        self.pls_components_spinbox.setMinimum(1); self.pls_components_spinbox.setMaximum(50); self.pls_components_spinbox.setValue(10)
        self.pls_components_spinbox.setObjectName("SpinBox")
        self.btn_train_pls = QPushButton("5. Train PLS Model")

        train_layout.addWidget(self.btn_load_folder, 0, 0, 1, 2)
        train_layout.addWidget(lbl_step2, 1, 0, 1, 2)
        train_layout.addWidget(lbl_step3, 2, 0, 1, 2)
        train_layout.addWidget(self.component_selector_combo, 3, 0, 1, 2)
        train_layout.addWidget(lbl_step4, 4, 0)
        train_layout.addWidget(self.pls_components_spinbox, 4, 1)
        train_layout.addWidget(self.btn_train_pls, 5, 0, 1, 2)

        table_header_label = QLabel("Calibration Data"); table_header_label.setObjectName("PanelHeaderLabel")
        self.data_table = QTableWidget()
        self.data_table.itemChanged.connect(self.update_reference_value)

        perf_label = QLabel("Model Performance"); perf_label.setObjectName("PanelHeaderLabel")
        perf_layout = QGridLayout()
        self.lbl_r2, self.lbl_rmse = QLabel("R² (Test): N/A"), QLabel("RMSE (Test): N/A")
        self.lbl_r2.setObjectName("PerfLabel"); self.lbl_rmse.setObjectName("PerfLabel")
        perf_layout.addWidget(self.lbl_r2, 0, 0); perf_layout.addWidget(self.lbl_rmse, 0, 1)
        
        lp_layout.addLayout(train_layout)
        lp_layout.addWidget(table_header_label)
        lp_layout.addWidget(self.data_table)
        lp_layout.addWidget(perf_label)
        lp_layout.addLayout(perf_layout)

        self.btn_load_folder.clicked.connect(self.load_folder)
        self.btn_train_pls.clicked.connect(self.train_pls_model_action)
        
        right_panel = self._create_plot_panel()

        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 2)
        return main_widget

    def _create_plot_panel(self):
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

    @Slot(QTableWidgetItem)
    def update_component_value(self, item):
        row, col = item.row(), item.column()
        if row >= len(self.chemical_components): return

        new_value = item.text()
        comp_dict = self.chemical_components[row]
        
        if col == 0:
            old_name = comp_dict.get('name')
            if old_name == new_value: return
            comp_dict['name'] = new_value
            if old_name in self.pls_models:
                self.pls_models[new_value] = self.pls_models.pop(old_name)
            for spec_data in self.spectra_data.values():
                if old_name in spec_data['refs']:
                    spec_data['refs'][new_value] = spec_data['refs'].pop(old_name)
            self._update_all_dynamic_widgets()
        elif col == 1:
            comp_dict['abbrev'] = new_value
        elif col == 2:
            comp_dict['unit'] = new_value

    @Slot()
    def add_component(self):
        row_count = self.components_table.rowCount(); self.components_table.insertRow(row_count)
        new_comp_name = f"NewComponent{row_count+1}"
        self.chemical_components.append({'name': new_comp_name, 'abbrev': '', 'unit': ''})
        
        self.components_table.blockSignals(True)
        self.components_table.setItem(row_count, 0, QTableWidgetItem(new_comp_name))
        self.components_table.setItem(row_count, 1, QTableWidgetItem(""))
        self.components_table.setItem(row_count, 2, QTableWidgetItem(""))
        self.components_table.blockSignals(False)

        self._update_all_dynamic_widgets()

    @Slot()
    def remove_component(self):
        current_row = self.components_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a component to remove.")
            return
        comp_name_to_remove = self.chemical_components[current_row]['name']
        del self.chemical_components[current_row]
        if comp_name_to_remove in self.pls_models:
            del self.pls_models[comp_name_to_remove]
        for spec_data in self.spectra_data.values():
            if comp_name_to_remove in spec_data['refs']:
                del spec_data['refs'][comp_name_to_remove]
        self.components_table.removeRow(current_row)
        self._update_all_dynamic_widgets()

    def _update_all_dynamic_widgets(self):
        self.components_table.blockSignals(True)
        self.components_table.setRowCount(len(self.chemical_components))
        for i, comp in enumerate(self.chemical_components):
            self.components_table.setItem(i, 0, QTableWidgetItem(comp['name']))
            self.components_table.setItem(i, 1, QTableWidgetItem(comp.get('abbrev', '')))
            self.components_table.setItem(i, 2, QTableWidgetItem(comp.get('unit', '')))
        self.components_table.blockSignals(False)
        self._update_data_table_columns()
        self.component_selector_combo.clear()
        self.component_selector_combo.addItems([comp['name'] for comp in self.chemical_components])

    def _update_data_table_columns(self):
        headers = ["Filename"] + [comp['name'] for comp in self.chemical_components]
        self.data_table.setColumnCount(len(headers))
        self.data_table.setHorizontalHeaderLabels(headers)
        self.data_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._populate_data_table_rows()

    def _populate_data_table_rows(self):
        self.data_table.blockSignals(True)
        self.data_table.setRowCount(len(self.spectra_data))
        sorted_filenames = sorted(self.spectra_data.keys())
        for i, filename in enumerate(sorted_filenames):
            item_filename = QTableWidgetItem(filename)
            item_filename.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.data_table.setItem(i, 0, item_filename)
            for j, comp in enumerate(self.chemical_components):
                ref_value = self.spectra_data[filename]['refs'].get(comp['name'])
                val_str = f"{ref_value:.4f}" if ref_value is not None else ""
                self.data_table.setItem(i, j + 1, QTableWidgetItem(val_str))
        self.data_table.blockSignals(False)

    @Slot(QTableWidgetItem)
    def update_reference_value(self, item):
        col_idx = item.column()
        if col_idx == 0: return
        row_idx = item.row()
        filename = self.data_table.item(row_idx, 0).text()
        comp_name = self.chemical_components[col_idx - 1]['name']
        try:
            value_str = item.text().strip()
            new_value = float(value_str) if value_str else None
            self.spectra_data[filename]['refs'][comp_name] = new_value
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number.")
            old_value = self.spectra_data[filename]['refs'].get(comp_name)
            item.setText(f"{old_value:.4f}" if old_value is not None else "")

    def load_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder Containing .spa Files")
        if not folder_path: return
        self.spectra_data = load_spectra_from_folder(folder_path)
        self._update_data_table_columns()
        self.reset_plot()
        QMessageBox.information(self, "Success", f"Loaded {len(self.spectra_data)} spectra.")

    def train_pls_model_action(self):
        target_component = self.component_selector_combo.currentText()
        if not target_component:
            QMessageBox.warning(self, "Warning", "Please define and select a component to model.")
            return
        
        num_components = self.pls_components_spinbox.value()
        model, scaler, r2, rmse = train_pls_model(self.spectra_data, target_component, num_components, self.current_derivative)

        if model is None:
            QMessageBox.warning(self, "Not Enough Data", rmse) # rmse contains the error message here
            return

        self.pls_models[target_component] = {'model': model, 'scaler': scaler}
        self.lbl_r2.setText(f"R² ({target_component}): {r2:.4f}")
        self.lbl_rmse.setText(f"RMSE ({target_component}): {rmse:.4f}")
        QMessageBox.information(self, "Training Complete", f"Model for '{target_component}' has been trained.")

    def _style_matplotlib_toolbar(self):
        icon_color = QColor(UP_DARK_GRAY)
        for action in self.toolbar.actions():
            if action.icon() and not action.icon().isNull():
                pixmap = action.icon().pixmap(32, 32)
                painter = QPainter(pixmap)
                painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
                painter.fillRect(pixmap.rect(), icon_color)
                painter.end()
                action.setIcon(QIcon(pixmap))

    def apply_derivative(self, deriv_order):
        self.current_derivative = deriv_order
        self.plot_spectra()

    def plot_spectra(self):
        self.ax.clear()
        if not self.spectra_data:
            self.ax.text(0.5, 0.5, 'No data loaded', ha='center')
            self.canvas.draw()
            return
            
        for filename, data in self.spectra_data.items():
            processed_intensity = get_processed_intensity(data['intensity'], self.current_derivative)
            self.ax.plot(data['nd'].x.data, processed_intensity, label=filename)
            
        if self.current_derivative == 0:
            title = "Original Spectra"
        elif self.current_derivative == 1:
            title = "1st Derivative"
        else:
            title = "2nd Derivative"
            
        self.ax.set_title(f"Spectra Viewer: {title}", fontsize=16, color=UP_MAROON, weight='bold')
        self.ax.set_xlabel('Wavenumber (cm⁻¹)')
        self.ax.set_ylabel('Absorbance / Intensity')
        self.ax.invert_xaxis()
        self.ax.set_facecolor(UP_WHITE)
        self.ax.grid(True, linestyle='--', color=UP_DARK_GRAY, alpha=0.3)
        self.ax.tick_params(colors=UP_DARK_GRAY)
        for spine in self.ax.spines.values():
            spine.set_edgecolor(UP_DARK_GRAY)
            
        if len(self.spectra_data) <= 20 and self.legend_visible:
            self.ax.legend(fontsize='small')
            
        self.fig.tight_layout()
        self.canvas.draw()

    def reset_plot(self):
        self.current_derivative = 0
        self.plot_spectra()

    def toggle_legend(self):
        self.legend_visible = not self.legend_visible
        self.plot_spectra()
