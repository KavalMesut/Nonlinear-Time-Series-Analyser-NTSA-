"""
Quick test to see console output
"""
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

app = QApplication(sys.argv)
window = MainWindow()
window.showMaximized()

print("=" * 60)
print("Application started. Test workflow:")
print("1. Load data (generate Lorenz system)")
print("2. Go to Linear Analysis")
print("3. Click Calculate (ACF)")
print("4. Watch console for DEBUG messages")
print("=" * 60)

app.exec()
