
# Entry point for the IRIS-UPLB Chemometrics application.
# This script initializes the Qt application, applies the custom stylesheet, and launches the main window.

import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import SpectraViewer
from ui.stylesheet import STYLESHEET

def main():
    """
    Main function to start the Chemometrics application.
    Initializes the QApplication, applies the stylesheet, and displays the main window.
    """
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = SpectraViewer()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
