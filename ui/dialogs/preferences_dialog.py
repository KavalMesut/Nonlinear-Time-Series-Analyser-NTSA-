"""
Preferences dialog
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt


class PreferencesDialog(QDialog):
    """Preferences dialog for settings"""
    
    def __init__(self, parent, theme_manager, translation_manager):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.tm = translation_manager
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle(self.tm('pref_title'))
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Appearance group
        appearance_group = QGroupBox(self.tm('pref_appearance'))
        appearance_layout = QFormLayout()
        
        # Theme selector
        self.theme_combo = QComboBox()
        self.theme_combo.addItem(self.tm('theme_dark'), 'dark')
        self.theme_combo.addItem(self.tm('theme_high_contrast'), 'high_contrast')
        self.theme_combo.addItem(self.tm('theme_scientific'), 'scientific')
        
        # Set current theme
        current_theme = self.theme_manager.current_theme
        index = self.theme_combo.findData(current_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        appearance_layout.addRow(self.tm('pref_theme') + ':', self.theme_combo)
        
        # Language selector
        self.language_combo = QComboBox()
        self.language_combo.addItem(self.tm('lang_turkish'), 'tr')
        self.language_combo.addItem(self.tm('lang_english'), 'en')
        
        # Set current language
        current_lang = self.tm.current_language
        lang_index = self.language_combo.findData(current_lang)
        if lang_index >= 0:
            self.language_combo.setCurrentIndex(lang_index)
        
        appearance_layout.addRow(self.tm('pref_language') + ':', self.language_combo)
        
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        restore_button = QPushButton(self.tm('pref_restore_defaults'))
        restore_button.clicked.connect(self.restore_defaults)
        button_layout.addWidget(restore_button)
        
        cancel_button = QPushButton(self.tm('btn_cancel'))
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        save_button = QPushButton(self.tm('pref_save'))
        save_button.clicked.connect(self.accept)
        save_button.setDefault(True)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
    
    def get_selected_theme(self) -> str:
        """Get selected theme"""
        return self.theme_combo.currentData()
    
    def get_selected_language(self) -> str:
        """Get selected language"""
        return self.language_combo.currentData()
    
    def restore_defaults(self):
        """Restore default settings"""
        self.theme_combo.setCurrentIndex(0)  # Dark theme
        lang_index = self.language_combo.findData('tr')
        if lang_index >= 0:
            self.language_combo.setCurrentIndex(lang_index)
