
# --- UP Visual Identity Color Palette ---
UP_MAROON, UP_FOREST_GREEN, UP_GOLD = "#8A1538", "#134633", "#FFB81C"
UP_WHITE, UP_LIGHT_GRAY, UP_DARK_GRAY, UP_MEDIUM_GRAY = "#FFFFFF", "#F0F0F0", "#333333", "#C0C0C0"

STYLESHEET = f"""
    /* --- General and Tab Styling --- */
    QMainWindow, QWidget {{ background-color: {UP_LIGHT_GRAY}; font-family: Segoe UI, Arial, sans-serif; }}
    QTabWidget::pane {{ border: none; }}
    QTabBar::tab {{
        background: {UP_MEDIUM_GRAY}; color: {UP_DARK_GRAY}; padding: 10px;
        font-weight: bold; border-top-left-radius: 5px; border-top-right-radius: 5px;
        min-width: 100px; margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background: {UP_FOREST_GREEN}; color: {UP_WHITE}; border-bottom: 3px solid {UP_GOLD};
    }}
    #TabTitle {{ font-size: 14pt; color: {UP_DARK_GRAY}; font-weight: bold; padding-bottom: 10px; }}

    /* --- Panel Styling --- */
    #ControlPanel {{ background-color: {UP_MAROON}; border-radius: 5px; }}
    #ControlPanel QLabel {{ color: {UP_WHITE}; }}
    #PanelHeaderLabel {{
        background-color: {UP_FOREST_GREEN}; color: {UP_WHITE}; font-size: 10pt; font-weight: bold;
        padding: 8px; border-radius: 5px; qproperty-alignment: 'AlignCenter';
    }}
    
    /* --- Widget Styling --- */
    QPushButton {{
        background-color: {UP_FOREST_GREEN}; color: {UP_WHITE}; font-size: 10pt; font-weight: bold;
        border: 1px solid {UP_GOLD}; border-radius: 5px; padding: 8px;
    }}
    QPushButton:hover {{ background-color: #1A5C40; }}
    QPushButton:pressed {{ background-color: #0E3827; }}
    #PerfLabel {{ color: {UP_WHITE}; font-size: 10pt; font-weight: bold; background-color: transparent; }}
    
    /* --- Table Styling --- */
    QTableWidget {{ background-color: {UP_WHITE}; color: {UP_DARK_GRAY}; border: none; gridline-color: {UP_LIGHT_GRAY}; }}
    QTableWidget::item:selected {{ background-color: {UP_FOREST_GREEN}; color: {UP_WHITE}; }}
    QHeaderView::section {{
        background-color: {UP_FOREST_GREEN}; color: {UP_WHITE}; padding: 5px;
        font-size: 10pt; font-weight: bold; border: none;
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

    QComboBox::drop-down {{ border: none; }}

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
    
    /* --- Other --- */
    QSplitter::handle {{ background-color: {UP_LIGHT_GRAY}; }}
    QSplitter::handle:horizontal {{ width: 5px; }}
    QToolBar {{ background-color: {UP_LIGHT_GRAY}; border: none; }}
    QToolButton:hover {{ background-color: {UP_MEDIUM_GRAY}; border-radius: 3px; }}
    QToolButton:checked {{ background-color: {UP_FOREST_GREEN}; border-radius: 3px; }}
"""
