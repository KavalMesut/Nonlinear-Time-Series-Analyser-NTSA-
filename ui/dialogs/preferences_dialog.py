"""
Preferences dialog
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QFormLayout,
    QSpinBox, QSlider, QCheckBox, QColorDialog, QTabWidget, QWidget
)
from PySide6.QtCore import Qt, Signal, QTimer
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
        
        # Throttle timer for live updates
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.setInterval(100)  # 100ms delay
        self.update_timer.timeout.connect(self._apply_and_emit)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle(self.tm('pref_title'))
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        # Apply current theme stylesheet to dialog
        current_theme = self.theme_manager.get_theme()
        self.setStyleSheet(current_theme.get_stylesheet())
        
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
        
        tabs.addTab(general_tab, "General")
        
        # Plot settings tab
        plot_tab = QWidget()
        plot_layout = QVBoxLayout(plot_tab)
        
        # Line settings group
        line_group = QGroupBox("Line Settings")
        line_layout = QFormLayout()
        
        # Line color
        self.line_color_btn = QPushButton()
        self.line_color = self.plot_settings.get_color('line_color')
        self.update_color_button(self.line_color_btn, self.line_color)
        self.line_color_btn.clicked.connect(lambda: self.choose_color('line'))
        line_layout.addRow("Line Color:", self.line_color_btn)
        
        # Line width
        line_width_label_layout = QHBoxLayout()
        line_width_label_layout.addWidget(QLabel("Line Width:"))
        self.line_width_label = QLabel(f"{self.plot_settings.get('line_width')} px")
        line_width_label_layout.addStretch()
        line_width_label_layout.addWidget(self.line_width_label)
        line_layout.addRow(line_width_label_layout)
        
        self.line_width_slider = QSlider(Qt.Horizontal)
        self.line_width_slider.setRange(1, 5)
        self.line_width_slider.setValue(self.plot_settings.get('line_width'))
        self.line_width_slider.setTickPosition(QSlider.TicksBelow)
        self.line_width_slider.setTickInterval(1)
        self.line_width_slider.valueChanged.connect(self.update_line_width_label)
        self.line_width_slider.valueChanged.connect(self.on_plot_setting_changed)
        line_layout.addRow(self.line_width_slider)
        
        line_group.setLayout(line_layout)
        plot_layout.addWidget(line_group)
        
        # Scatter settings group
        scatter_group = QGroupBox("Point Settings")
        scatter_layout = QFormLayout()
        
        # Scatter size
        scatter_size_label_layout = QHBoxLayout()
        scatter_size_label_layout.addWidget(QLabel("Point Size:"))
        self.scatter_size_label = QLabel(f"{self.plot_settings.get('scatter_size')} px")
        scatter_size_label_layout.addStretch()
        scatter_size_label_layout.addWidget(self.scatter_size_label)
        scatter_layout.addRow(scatter_size_label_layout)
        
        self.scatter_size_slider = QSlider(Qt.Horizontal)
        self.scatter_size_slider.setRange(2, 10)
        self.scatter_size_slider.setValue(self.plot_settings.get('scatter_size'))
        self.scatter_size_slider.setTickPosition(QSlider.TicksBelow)
        self.scatter_size_slider.setTickInterval(1)
        self.scatter_size_slider.valueChanged.connect(self.update_scatter_size_label)
        self.scatter_size_slider.valueChanged.connect(self.on_plot_setting_changed)
        scatter_layout.addRow(self.scatter_size_slider)
        
        scatter_group.setLayout(scatter_layout)
        plot_layout.addWidget(scatter_group)
        
        # Grid settings group
        grid_group = QGroupBox("Grid Settings")
        grid_layout = QVBoxLayout()
        
        # Grid alpha slider
        grid_label_layout = QHBoxLayout()
        grid_label_layout.addWidget(QLabel("Grid Opacity:"))
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
        axis_group = QGroupBox("Axis Settings")
        axis_layout = QFormLayout()
        
        # Axis color
        self.axis_color_btn = QPushButton()
        self.axis_color = self.plot_settings.get_color('axis_color')
        self.update_color_button(self.axis_color_btn, self.axis_color)
        self.axis_color_btn.clicked.connect(lambda: self.choose_color('axis'))
        axis_layout.addRow("Axis Color:", self.axis_color_btn)
        
        # Font size
        font_size_label_layout = QHBoxLayout()
        font_size_label_layout.addWidget(QLabel("Font Size:"))
        self.font_size_label = QLabel(f"{self.plot_settings.get('font_size')} pt")
        font_size_label_layout.addStretch()
        font_size_label_layout.addWidget(self.font_size_label)
        axis_layout.addRow(font_size_label_layout)
        
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setRange(8, 16)
        self.font_size_slider.setValue(self.plot_settings.get('font_size'))
        self.font_size_slider.setTickPosition(QSlider.TicksBelow)
        self.font_size_slider.setTickInterval(1)
        self.font_size_slider.valueChanged.connect(self.update_font_size_label)
        self.font_size_slider.valueChanged.connect(self.on_plot_setting_changed)
        axis_layout.addRow(self.font_size_slider)
        
        axis_group.setLayout(axis_layout)
        plot_layout.addWidget(axis_group)
        
        # 3D settings group
        d3_group = QGroupBox("3D Plot Settings")
        d3_layout = QFormLayout()
        
        # 3D scatter size
        scatter_3d_size_label_layout = QHBoxLayout()
        scatter_3d_size_label_layout.addWidget(QLabel("3D Point Size:"))
        self.scatter_3d_size_label = QLabel(f"{self.plot_settings.get('scatter_3d_size')} px")
        scatter_3d_size_label_layout.addStretch()
        scatter_3d_size_label_layout.addWidget(self.scatter_3d_size_label)
        d3_layout.addRow(scatter_3d_size_label_layout)
        
        self.scatter_3d_size_slider = QSlider(Qt.Horizontal)
        self.scatter_3d_size_slider.setRange(1, 8)
        self.scatter_3d_size_slider.setValue(self.plot_settings.get('scatter_3d_size'))
        self.scatter_3d_size_slider.setTickPosition(QSlider.TicksBelow)
        self.scatter_3d_size_slider.setTickInterval(1)
        self.scatter_3d_size_slider.valueChanged.connect(self.update_scatter_3d_size_label)
        self.scatter_3d_size_slider.valueChanged.connect(self.on_plot_setting_changed)
        d3_layout.addRow(self.scatter_3d_size_slider)
        
        # 3D trajectory width
        trajectory_3d_width_label_layout = QHBoxLayout()
        trajectory_3d_width_label_layout.addWidget(QLabel("3D Trajectory Width:"))
        self.trajectory_3d_width_label = QLabel(f"{self.plot_settings.get('trajectory_3d_width')} px")
        trajectory_3d_width_label_layout.addStretch()
        trajectory_3d_width_label_layout.addWidget(self.trajectory_3d_width_label)
        d3_layout.addRow(trajectory_3d_width_label_layout)
        
        self.trajectory_3d_width_slider = QSlider(Qt.Horizontal)
        self.trajectory_3d_width_slider.setRange(1, 5)
        self.trajectory_3d_width_slider.setValue(self.plot_settings.get('trajectory_3d_width'))
        self.trajectory_3d_width_slider.setTickPosition(QSlider.TicksBelow)
        self.trajectory_3d_width_slider.setTickInterval(1)
        self.trajectory_3d_width_slider.valueChanged.connect(self.update_trajectory_3d_width_label)
        self.trajectory_3d_width_slider.valueChanged.connect(self.on_plot_setting_changed)
        d3_layout.addRow(self.trajectory_3d_width_slider)
        
        d3_group.setLayout(d3_layout)
        plot_layout.addWidget(d3_group)
        
        # Other settings group
        other_group = QGroupBox("Other Settings")
        other_layout = QFormLayout()
        
        # Anti-aliasing
        self.antialiasing_check = QCheckBox()
        self.antialiasing_check.setChecked(self.plot_settings.get('antialiasing'))
        self.antialiasing_check.stateChanged.connect(self.on_plot_setting_changed)
        other_layout.addRow("Anti-aliasing:", self.antialiasing_check)
        
        other_group.setLayout(other_layout)
        plot_layout.addWidget(other_group)
        
        plot_layout.addStretch()
        
        tabs.addTab(plot_tab, "Plot Settings")
        
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
        self.line_width_slider.setValue(self.plot_settings.get('line_width'))
        self.scatter_size_slider.setValue(self.plot_settings.get('scatter_size'))
        self.grid_alpha_slider.setValue(self.plot_settings.get('grid_alpha'))
        self.axis_color = self.plot_settings.get_color('axis_color')
        self.update_color_button(self.axis_color_btn, self.axis_color)
        self.font_size_slider.setValue(self.plot_settings.get('font_size'))
        self.scatter_3d_size_slider.setValue(self.plot_settings.get('scatter_3d_size'))
        self.trajectory_3d_width_slider.setValue(self.plot_settings.get('trajectory_3d_width'))
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
        
        color = QColorDialog.getColor(current_color, self, "Pick Color")
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
    
    def update_line_width_label(self, value: int):
        """Update line width label"""
        self.line_width_label.setText(f"{value} px")
    
    def update_scatter_size_label(self, value: int):
        """Update scatter size label"""
        self.scatter_size_label.setText(f"{value} px")
    
    def update_font_size_label(self, value: int):
        """Update font size label"""
        self.font_size_label.setText(f"{value} pt")
    
    def update_scatter_3d_size_label(self, value: int):
        """Update 3D scatter size label"""
        self.scatter_3d_size_label.setText(f"{value} px")
    
    def update_trajectory_3d_width_label(self, value: int):
        """Update 3D trajectory width label"""
        self.trajectory_3d_width_label.setText(f"{value} px")
    
    def on_plot_setting_changed(self):
        """Called when any plot setting changes - throttled update"""
        # Restart timer (debounce rapid changes)
        self.update_timer.stop()
        self.update_timer.start()
    
    def _apply_and_emit(self):
        """Actually apply settings and emit signal (throttled)"""
        self.apply_plot_settings()
        self.plot_settings_changed.emit()
    
    def apply_plot_settings(self):
        """Apply plot settings to PlotSettings object"""
        self.plot_settings.set_color('line_color', self.line_color)
        self.plot_settings.set('line_width', self.line_width_slider.value())
        self.plot_settings.set('scatter_size', self.scatter_size_slider.value())
        self.plot_settings.set('grid_alpha', self.grid_alpha_slider.value())
        self.plot_settings.set_color('axis_color', self.axis_color)
        self.plot_settings.set('font_size', self.font_size_slider.value())
        self.plot_settings.set('scatter_3d_size', self.scatter_3d_size_slider.value())
        self.plot_settings.set('trajectory_3d_width', self.trajectory_3d_width_slider.value())
        self.plot_settings.set('antialiasing', self.antialiasing_check.isChecked())
        # Don't save yet - save only on dialog accept
