"""
Main application launcher
"""
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """Launch application"""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("Nonlinear Time Series Analyzer")
    app.setOrganizationName("TSAnalyzer")
    app.setApplicationVersion("1.0.0")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
