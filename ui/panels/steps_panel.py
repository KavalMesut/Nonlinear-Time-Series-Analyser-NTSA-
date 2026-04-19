"""
Steps panel - left sidebar showing analysis steps
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, 
    QListWidgetItem, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont


class StepsPanel(QWidget):
    """Left panel showing analysis steps"""
    
    step_selected = Signal(int)
    
    def __init__(self, translation_manager):
        super().__init__()
        self.tm = translation_manager
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel(self.tm('panel_steps'))
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Steps list
        self.steps_list = QListWidget()
        self.steps_list.currentRowChanged.connect(self.on_step_selected)
        
        # Add steps
        self.steps = [
            ('step_data_load', True),
            ('step_preprocessing', False),
            ('step_linear_analysis', False),
            ('step_parameter_estimation', False),
            ('step_embedding', False),
            ('step_chaos_analysis', False),
            ('step_results', False)
        ]
        
        for step_key, unlocked in self.steps:
            item = QListWidgetItem(self.tm(step_key))
            if not unlocked:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.steps_list.addItem(item)
        
        layout.addWidget(self.steps_list)
        
        # Status label
        self.status_label = QLabel(self.tm('status_locked'))
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def on_step_selected(self, index):
        """Handle step selection"""
        if index >= 0:
            self.step_selected.emit(index)
            self.update_status(index)
            
            # Update content panel if accessible
            try:
                main_window = self.window()
                if hasattr(main_window, 'content_panel'):
                    main_window.content_panel.set_step(index)
            except:
                pass
    
    def update_status(self, index):
        """Update status label"""
        if index >= 0 and index < len(self.steps):
            _, unlocked = self.steps[index]
            if unlocked:
                self.status_label.setText(self.tm('status_unlocked'))
            else:
                self.status_label.setText(self.tm('status_locked'))
    
    def unlock_step(self, index):
        """Unlock a step"""
        if index >= 0 and index < len(self.steps):
            self.steps[index] = (self.steps[index][0], True)
            item = self.steps_list.item(index)
            item.setFlags(item.flags() | Qt.ItemIsEnabled)
    
    def lock_step(self, index):
        """Lock a step"""
        if index >= 0 and index < len(self.steps):
            self.steps[index] = (self.steps[index][0], False)
            item = self.steps_list.item(index)
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
    
    def refresh_ui(self):
        """Refresh UI with current language"""
        # Update all step labels
        for i, (step_key, _) in enumerate(self.steps):
            item = self.steps_list.item(i)
            item.setText(self.tm(step_key))
        
        # Update title and status
        self.findChild(QLabel).setText(self.tm('panel_steps'))
        current = self.steps_list.currentRow()
        if current >= 0:
            self.update_status(current)
