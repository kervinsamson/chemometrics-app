
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import SpectraViewer
from ui.stylesheet import STYLESHEET

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = SpectraViewer()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
