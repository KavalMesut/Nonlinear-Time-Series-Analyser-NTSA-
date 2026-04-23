"""Test spinbox up/down arrows"""
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QSpinBox, QLabel
from PySide6.QtCore import Signal
import sys

class TestDialog(QDialog):
    value_changed = Signal(int)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SpinBox Test")
        layout = QVBoxLayout(self)
        
        self.label = QLabel("Value: 2")
        layout.addWidget(self.label)
        
        self.spin = QSpinBox()
        self.spin.setRange(1, 5)
        self.spin.setValue(2)
        self.spin.setSuffix(" px")
        self.spin.valueChanged.connect(self.on_value_changed)
        layout.addWidget(self.spin)
        
        self.count_label = QLabel("Changes: 0")
        layout.addWidget(self.count_label)
        
        self.changes = 0
    
    def on_value_changed(self, value):
        self.changes += 1
        self.label.setText(f"Value: {value}")
        self.count_label.setText(f"Changes: {self.changes}")
        self.value_changed.emit(value)
        print(f"SpinBox value changed to: {value}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    dialog = TestDialog()
    dialog.value_changed.connect(lambda v: print(f"Signal received: {v}"))
    dialog.show()
    
    sys.exit(app.exec())
