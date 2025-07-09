# --- UP Visual Identity Color Palette ---
UP_MAROON, UP_FOREST_GREEN, UP_GOLD = "#8A1538", "#134633", "#FFB81C"
UP_WHITE, UP_LIGHT_GRAY, UP_DARK_GRAY, UP_MEDIUM_GRAY = "#FFFFFF", "#F0F0F0", "#333333", "#C0C0C0"

STYLESHEET = f"""
    /* --- General and Tab Styling --- */
    QMainWindow, QWidget {{ background-color: {UP_LIGHT_GRAY}; font-family: Segoe UI, Arial, sans-serif; }}
    QTabWidget {{ margin: 0px; padding: 0px; }}
    QTabWidget::pane {{ border: none; margin: 0px; padding: 0px; }}
    QTabBar {{ margin: 0px; padding: 0px; }}
    QTabBar::tab {{
        background: {UP_MEDIUM_GRAY}; color: {UP_DARK_GRAY}; padding: 10px;
        font-weight: bold;
        min-width: 100px; margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background: {UP_FOREST_GREEN}; color: {UP_WHITE}; border-bottom: 3px solid {UP_GOLD};
    }}
    #TabTitle {{ font-size: 14pt; color: {UP_DARK_GRAY}; font-weight: bold; padding-bottom: 10px; }}

    /* --- Panel Styling --- */
    #ControlPanel {{ 
        background-color: {UP_MAROON}; 
        min-width: 371px;
        margin-left: -12px;
    }}
    #PanelHeaderLabel {{
        background-color: {UP_FOREST_GREEN}; color: {UP_WHITE}; font-size: 10pt; font-weight: bold;
        padding: 8px; border-radius: 5px; qproperty-alignment: 'AlignCenter';
    }}
    
    #ResultsPanel {{
        background-color: {UP_WHITE};
        border-radius: 5px;
    }}

    /* --- Widget Styling --- */
    QPushButton {{
        background-color: {UP_FOREST_GREEN}; color: {UP_WHITE}; font-size: 10pt; font-weight: bold;
        border: 1px solid {UP_GOLD}; border-radius: 5px; padding: 8px;
    }}
    QPushButton:hover {{ background-color: #1A5C40; }}
    QPushButton:pressed {{ background-color: #0E3827; }}
    
    /* --- NEW: Styling for checkable buttons (derivative buttons) --- */
    QPushButton:checked {{
        background-color: {UP_GOLD}; 
        color: {UP_DARK_GRAY}; 
        border: 2px solid {UP_FOREST_GREEN};
        font-weight: bold;
    }}
    QPushButton:checked:hover {{
        background-color: #E6A519; /* Slightly darker gold on hover */
    }}
    /* --- END NEW --- */
    
    #PerfLabel {{ color: {UP_WHITE}; font-size: 10pt; font-weight: bold; background-color: transparent; }}
    
    /* --- Table Styling --- */
    QTableWidget {{ background-color: {UP_WHITE}; color: {UP_DARK_GRAY}; border: none; gridline-color: {UP_LIGHT_GRAY}; }}
    QTableWidget::item:selected {{ background-color: {UP_FOREST_GREEN}; color: {UP_WHITE}; }}
    
    /* --- FIX for unreadable text during editing --- */
    QTableWidget QLineEdit {{
        color: {UP_DARK_GRAY};
        background-color: {UP_WHITE};
    }}
    
    QHeaderView::section {{
        background-color: {UP_FOREST_GREEN}; color: {UP_WHITE}; padding: 5px;
        font-size: 10pt; font-weight: bold; border: none;
    }}

    /* --- Style for the Prediction Table Header --- */
    #PredictionTable QHeaderView::section {{
        background-color: {UP_DARK_GRAY};
        color: {UP_WHITE};
        font-size: 11pt;
        padding: 8px;
    }}
    
    /* --- FINAL CORRECTED SPINBOX AND COMBOBOX STYLING --- */
    QSpinBox, QComboBox {{
        background-color: {UP_WHITE};
        color: {UP_DARK_GRAY};
        border: 2px solid {UP_GOLD};
        border-radius: 5px;
        padding: 5px;
        font-weight: bold;
        min-height: 24px;
    }}

    QComboBox::drop-down {{ 
        border: none; 
        width: 20px;
        subcontrol-origin: padding;
        subcontrol-position: top right;
        background-color: {UP_MEDIUM_GRAY};
        border-left: 1px solid {UP_GOLD};
        border-top-right-radius: 3px;
        border-bottom-right-radius: 3px;
    }}
    
    QComboBox::drop-down:hover {{
        background-color: {UP_FOREST_GREEN};
    }}
    
    /* Hide the arrow completely for a cleaner look */
    QComboBox::down-arrow {{
        image: none;
        width: 0px;
        height: 0px;
        border: none;
    }}
    
    /* Fix dropdown list items to be readable */
    QComboBox QAbstractItemView {{
        background-color: {UP_WHITE};
        color: {UP_DARK_GRAY};
        border: 2px solid {UP_GOLD};
        selection-background-color: {UP_FOREST_GREEN};
        selection-color: {UP_WHITE};
        font-weight: bold;
    }}
    
    QComboBox QAbstractItemView::item {{
        background-color: {UP_WHITE};
        color: {UP_DARK_GRAY};
        padding: 8px;
        border: none;
    }}
    
    QComboBox QAbstractItemView::item:selected {{
        background-color: {UP_FOREST_GREEN};
        color: {UP_WHITE};
    }}
    
    QComboBox QAbstractItemView::item:hover {{
        background-color: {UP_LIGHT_GRAY};
        color: {UP_DARK_GRAY};
    }}

    /* --- THE FIX IS HERE: SIMPLIFIED BUTTON STYLING --- */
    
    /* General properties for both buttons */
    QSpinBox::up-button, QSpinBox::down-button {{
        subcontrol-origin: border;
        background-color: {UP_MEDIUM_GRAY};
        width: 18px;
        border-left: 1px solid {UP_GOLD};
    }}
    
    /* Hover state for both buttons */
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: {UP_FOREST_GREEN};
    }}

    /* Position the up button at the top right */
    QSpinBox::up-button {{
        subcontrol-position: top right;
        border-top-right-radius: 3px;
    }}

    /* Position the down button at the bottom right */
    QSpinBox::down-button {{
        subcontrol-position: bottom right;
        border-bottom-right-radius: 3px;
    }}
    
    /*
    * BY NOT SPECIFYING a style for 'QSpinBox::up-arrow' or 'QSpinBox::down-arrow',
    * we let Qt draw its default system arrow, which is visible.
    * This is the simplest and most robust solution.
    */
    
    /* --- Style for the auto PLS component selection checkbox --- */
    QCheckBox {{
        spacing: 8px;
        color: {UP_DARK_GRAY};
        font-weight: bold;
        font-size: 10pt;
    }}
    
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {UP_GOLD};
        border-radius: 3px;
        background-color: {UP_WHITE};
    }}
    
    QCheckBox::indicator:hover {{
        border-color: {UP_FOREST_GREEN};
        background-color: {UP_LIGHT_GRAY};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {UP_FOREST_GREEN};
        border-color: {UP_GOLD};
    }}
    
    QCheckBox::indicator:checked:hover {{
        background-color: #1A5C40;
        border-color: {UP_GOLD};
    }}
    
    QCheckBox::indicator:unchecked {{
        background-color: {UP_WHITE};
        border-color: {UP_GOLD};
    }}
    
    QCheckBox::indicator:unchecked:hover {{
        background-color: {UP_LIGHT_GRAY};
        border-color: {UP_FOREST_GREEN};
    }}



    /* --- Style for QLineEdit (text input fields) --- */
    QLineEdit {{
        background-color: {UP_WHITE};
        color: {UP_DARK_GRAY};
        border: 2px solid {UP_GOLD};
        border-radius: 5px;
        padding: 5px;
        font-weight: bold;
        min-height: 24px;
    }}
    
    QLineEdit:focus {{
        border-color: {UP_FOREST_GREEN};
    }}
    
    QLineEdit:hover {{
        border-color: #1A5C40;
    }}
    
    /* --- Other --- */
    QSplitter::handle {{ 
        background-color: {UP_LIGHT_GRAY}; 
        border: none;
    }}
    QSplitter::handle:horizontal {{ 
        width: 6px; 
        background-color: {UP_MEDIUM_GRAY};
        border-left: 1px solid {UP_MEDIUM_GRAY};
        border-right: 1px solid {UP_MEDIUM_GRAY};
    }}
    QSplitter::handle:horizontal:hover {{ 
        background-color: {UP_FOREST_GREEN}; 
        border-left: 1px solid {UP_GOLD};
        border-right: 1px solid {UP_GOLD};
    }}
    QToolBar {{ background-color: {UP_LIGHT_GRAY}; border: none; }}
    QToolButton:hover {{ background-color: {UP_MEDIUM_GRAY}; border-radius: 3px; }}
    QToolButton:checked {{ background-color: {UP_FOREST_GREEN}; border-radius: 3px; }}

    /* --- Custom Scrollbar Styling --- */
    QScrollBar:vertical {{
        background-color: {UP_LIGHT_GRAY};
        width: 14px;
        margin: 0px;
        border: none;
        border-radius: 7px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {UP_FOREST_GREEN};
        min-height: 30px;
        border-radius: 7px;
        margin: 2px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: #1A5C40;
    }}
    
    QScrollBar::handle:vertical:pressed {{
        background-color: #0E3827;
    }}
    
    /* Hide the arrow buttons completely for a cleaner look */
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
        subcontrol-origin: margin;
    }}
    
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    
    /* Horizontal scrollbar */
    QScrollBar:horizontal {{
        background-color: {UP_LIGHT_GRAY};
        height: 14px;
        margin: 0px;
        border: none;
        border-radius: 7px;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {UP_FOREST_GREEN};
        min-width: 30px;
        border-radius: 7px;
        margin: 2px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: #1A5C40;
    }}
    
    QScrollBar::handle:horizontal:pressed {{
        background-color: #0E3827;
    }}
    
    /* Hide the arrow buttons completely for a cleaner look */
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
        subcontrol-origin: margin;
    }}
    
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}

    /* --- QMessageBox Styling --- */
    QMessageBox {{
        background-color: {UP_LIGHT_GRAY};
    }}
    QMessageBox QLabel {{ /* Target the text label inside the message box */
        color: {UP_DARK_GRAY};
        font-size: 10pt;
    }}
    QMessageBox QPushButton {{ /* Style buttons specifically for the message box */
        background-color: {UP_FOREST_GREEN};
        color: {UP_WHITE};
        border: 1px solid {UP_GOLD};
        border-radius: 5px;
        padding: 8px;
        min-width: 80px; /* Ensure buttons have a decent size */
    }}
    QMessageBox QPushButton:hover {{
        background-color: #1A5C40;
    }}
    QMessageBox QPushButton:pressed {{
        background-color: #0E3827;
    }}
"""
