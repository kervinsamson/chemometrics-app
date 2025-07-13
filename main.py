
# Entry point for the IRIS-UPLB Chemometrics application.
# This script initializes the Qt application, applies the custom stylesheet, and launches the main window.

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.main_window import SpectraViewer
from ui.stylesheet import STYLESHEET

def main():
    """
    Main function to start the Chemometrics application.
    Initializes the QApplication, applies the stylesheet, and displays the main window.
    """
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    
    # Set application icon
    # Handle PyInstaller bundle and development paths
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        icon_path = os.path.join(sys._MEIPASS, "icon.ico")
    else:
        # Running in development
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = SpectraViewer()
    
    # Set window icon
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
