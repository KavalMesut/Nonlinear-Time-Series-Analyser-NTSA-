"""
Preferences dialog
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QFormLayout,
    QSpinBox, QSlider, QCheckBox, QColorDialog, QTabWidget, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor


class PreferencesDialog(QDialog):
    """Preferences dialog for settings"""
    
    # Signal emitted when plot settings change
    plot_settings_changed = Signal()
    
    def __init__(self, parent, theme_manager, translation_manager, plot_settings):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.tm = translation_manager
        self.plot_settings = plot_settings
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle(self.tm('pref_title'))
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # General tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
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
        general_layout.addWidget(appearance_group)
        general_layout.addStretch()
        
        tabs.addTab(general_tab, "Genel")
        
        # Plot settings tab
        plot_tab = QWidget()
        plot_layout = QVBoxLayout(plot_tab)
        
        # Line settings group
        line_group = QGroupBox("Çizgi Ayarları")
        line_layout = QFormLayout()
        
        # Line color
        self.line_color_btn = QPushButton()
        self.line_color = self.plot_settings.get_color('line_color')
        self.update_color_button(self.line_color_btn, self.line_color)
        self.line_color_btn.clicked.connect(lambda: self.choose_color('line'))
        line_layout.addRow("Çizgi Rengi:", self.line_color_btn)
        
        # Line width
        self.line_width_spin = QSpinBox()
        self.line_width_spin.setRange(1, 5)
        self.line_width_spin.setValue(self.plot_settings.get('line_width'))
        self.line_width_spin.setSuffix(" px")
        self.line_width_spin.valueChanged.connect(self.on_plot_setting_changed)
        line_layout.addRow("Çizgi Kalınlığı:", self.line_width_spin)
        
        line_group.setLayout(line_layout)
        plot_layout.addWidget(line_group)
        
        # Scatter settings group
        scatter_group = QGroupBox("Nokta Ayarları")
        scatter_layout = QFormLayout()
        
        # Scatter size
        self.scatter_size_spin = QSpinBox()
        self.scatter_size_spin.setRange(2, 10)
        self.scatter_size_spin.setValue(self.plot_settings.get('scatter_size'))
        self.scatter_size_spin.setSuffix(" px")
        self.scatter_size_spin.valueChanged.connect(self.on_plot_setting_changed)
        scatter_layout.addRow("Nokta Boyutu:", self.scatter_size_spin)
        
        scatter_group.setLayout(scatter_layout)
        plot_layout.addWidget(scatter_group)
        
        # Grid settings group
        grid_group = QGroupBox("Grid Ayarları")
        grid_layout = QVBoxLayout()
        
        # Grid alpha slider
        grid_label_layout = QHBoxLayout()
        grid_label_layout.addWidget(QLabel("Grid Şeffaflığı:"))
        self.grid_alpha_label = QLabel(f"{self.plot_settings.get('grid_alpha')}%")
        grid_label_layout.addStretch()
        grid_label_layout.addWidget(self.grid_alpha_label)
        grid_layout.addLayout(grid_label_layout)
        
        self.grid_alpha_slider = QSlider(Qt.Horizontal)
        self.grid_alpha_slider.setRange(10, 100)
        self.grid_alpha_slider.setSingleStep(10)
        self.grid_alpha_slider.setPageStep(10)
        self.grid_alpha_slider.setValue(self.plot_settings.get('grid_alpha'))
        self.grid_alpha_slider.setTickPosition(QSlider.TicksBelow)
        self.grid_alpha_slider.setTickInterval(10)
        self.grid_alpha_slider.valueChanged.connect(self.update_grid_alpha_label)
        self.grid_alpha_slider.valueChanged.connect(self.on_plot_setting_changed)
        grid_layout.addWidget(self.grid_alpha_slider)
        
        grid_group.setLayout(grid_layout)
        plot_layout.addWidget(grid_group)
        
        # Axis settings group
        axis_group = QGroupBox("Eksen Ayarları")
        axis_layout = QFormLayout()
        
        # Axis color
        self.axis_color_btn = QPushButton()
        self.axis_color = self.plot_settings.get_color('axis_color')
        self.update_color_button(self.axis_color_btn, self.axis_color)
        self.axis_color_btn.clicked.connect(lambda: self.choose_color('axis'))
        axis_layout.addRow("Eksen Rengi:", self.axis_color_btn)
        
        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(self.plot_settings.get('font_size'))
        self.font_size_spin.setSuffix(" pt")
        self.font_size_spin.valueChanged.connect(self.on_plot_setting_changed)
        axis_layout.addRow("Font Boyutu:", self.font_size_spin)
        
        axis_group.setLayout(axis_layout)
        plot_layout.addWidget(axis_group)
        
        # 3D settings group
        d3_group = QGroupBox("3D Grafik Ayarları")
        d3_layout = QFormLayout()
        
        # 3D scatter size
        self.scatter_3d_size_spin = QSpinBox()
        self.scatter_3d_size_spin.setRange(1, 8)
        self.scatter_3d_size_spin.setValue(self.plot_settings.get('scatter_3d_size'))
        self.scatter_3d_size_spin.setSuffix(" px")
        self.scatter_3d_size_spin.valueChanged.connect(self.on_plot_setting_changed)
        d3_layout.addRow("3D Nokta Boyutu:", self.scatter_3d_size_spin)
        
        # 3D trajectory width
        self.trajectory_3d_width_spin = QSpinBox()
        self.trajectory_3d_width_spin.setRange(1, 5)
        self.trajectory_3d_width_spin.setValue(self.plot_settings.get('trajectory_3d_width'))
        self.trajectory_3d_width_spin.setSuffix(" px")
        self.trajectory_3d_width_spin.valueChanged.connect(self.on_plot_setting_changed)
        d3_layout.addRow("3D Trajectory Kalınlığı:", self.trajectory_3d_width_spin)
        
        d3_group.setLayout(d3_layout)
        plot_layout.addWidget(d3_group)
        
        # Other settings group
        other_group = QGroupBox("Diğer Ayarlar")
        other_layout = QFormLayout()
        
        # Anti-aliasing
        self.antialiasing_check = QCheckBox()
        self.antialiasing_check.setChecked(self.plot_settings.get('antialiasing'))
        self.antialiasing_check.stateChanged.connect(self.on_plot_setting_changed)
        other_layout.addRow("Anti-aliasing:", self.antialiasing_check)
        
        other_group.setLayout(other_layout)
        plot_layout.addWidget(other_group)
        
        plot_layout.addStretch()
        
        tabs.addTab(plot_tab, "Grafik Ayarları")
        
        layout.addWidget(tabs)
        
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
        # General settings
        self.theme_combo.setCurrentIndex(0)  # Dark theme
        lang_index = self.language_combo.findData('tr')
        if lang_index >= 0:
            self.language_combo.setCurrentIndex(lang_index)
        
        # Plot settings
        self.plot_settings.reset_to_defaults()
        
        # Update UI with defaults
        self.line_color = self.plot_settings.get_color('line_color')
        self.update_color_button(self.line_color_btn, self.line_color)
        self.line_width_spin.setValue(self.plot_settings.get('line_width'))
        self.scatter_size_spin.setValue(self.plot_settings.get('scatter_size'))
        self.grid_alpha_slider.setValue(self.plot_settings.get('grid_alpha'))
        self.axis_color = self.plot_settings.get_color('axis_color')
        self.update_color_button(self.axis_color_btn, self.axis_color)
        self.font_size_spin.setValue(self.plot_settings.get('font_size'))
        self.scatter_3d_size_spin.setValue(self.plot_settings.get('scatter_3d_size'))
        self.trajectory_3d_width_spin.setValue(self.plot_settings.get('trajectory_3d_width'))
        self.antialiasing_check.setChecked(self.plot_settings.get('antialiasing'))
    
    def update_color_button(self, button: QPushButton, color: QColor):
        """Update color button appearance"""
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color.name()};
                border: 2px solid #555555;
                border-radius: 3px;
                min-width: 80px;
                min-height: 25px;
            }}
            QPushButton:hover {{
                border: 2px solid #777777;
            }}
        """)
        button.setText(color.name().upper())
    
    def choose_color(self, color_type: str):
        """Open color picker dialog"""
        if color_type == 'line':
            current_color = self.line_color
        elif color_type == 'axis':
            current_color = self.axis_color
        else:
            return
        
        color = QColorDialog.getColor(current_color, self, "Renk Seç")
        if color.isValid():
            if color_type == 'line':
                self.line_color = color
                self.update_color_button(self.line_color_btn, color)
            elif color_type == 'axis':
                self.axis_color = color
                self.update_color_button(self.axis_color_btn, color)
            
            # Trigger live update
            self.on_plot_setting_changed()
    
    def update_grid_alpha_label(self, value: int):
        """Update grid alpha label"""
        self.grid_alpha_label.setText(f"{value}%")
    
    def on_plot_setting_changed(self):
        """Called when any plot setting changes - apply and emit signal"""
        self.apply_plot_settings()
        self.plot_settings_changed.emit()
    
    def apply_plot_settings(self):
        """Apply plot settings to PlotSettings object"""
        self.plot_settings.set_color('line_color', self.line_color)
        self.plot_settings.set('line_width', self.line_width_spin.value())
        self.plot_settings.set('scatter_size', self.scatter_size_spin.value())
        self.plot_settings.set('grid_alpha', self.grid_alpha_slider.value())
        self.plot_settings.set_color('axis_color', self.axis_color)
        self.plot_settings.set('font_size', self.font_size_spin.value())
        self.plot_settings.set('scatter_3d_size', self.scatter_3d_size_spin.value())
        self.plot_settings.set('trajectory_3d_width', self.trajectory_3d_width_spin.value())
        self.plot_settings.set('antialiasing', self.antialiasing_check.isChecked())
        # Don't save yet - save only on dialog accept
