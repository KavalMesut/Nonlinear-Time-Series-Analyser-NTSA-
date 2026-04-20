"""
Data loading panel with drag-drop and file browser support
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QGroupBox, QFileDialog, QSpinBox,
    QDoubleSpinBox, QFormLayout, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
import os


class DataLoadPanel(QWidget):
    """Data loading panel with drag-drop and file selection"""
    
    data_loaded = Signal(object)  # Emits TimeSeries object
    
    def __init__(self, translation_manager):
        super().__init__()
        self.tm = translation_manager
        self.setAcceptDrops(True)  # Enable drag-drop
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Source selection
        source_group = QGroupBox(self.tm('data_source'))
        source_layout = QVBoxLayout()
        
        # Radio buttons for source type
        self.source_group = QButtonGroup()
        self.file_radio = QRadioButton(self.tm('data_load_file'))
        self.generate_radio = QRadioButton(self.tm('data_generate'))
        
        self.source_group.addButton(self.file_radio, 0)
        self.source_group.addButton(self.generate_radio, 1)
        self.file_radio.setChecked(True)
        
        self.file_radio.toggled.connect(self.on_source_changed)
        
        source_layout.addWidget(self.file_radio)
        source_layout.addWidget(self.generate_radio)
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # File loading group
        self.file_group = QGroupBox(self.tm('data_load_file'))
        file_layout = QVBoxLayout()
        
        # Drag-drop area
        self.drop_label = QLabel(self.tm('data_load_file') + '\n\n' + 
                                 '📁 ' + self.tm('data_browse') + '\n' +
                                 '🔽 ' + 'Drag & Drop')
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setMinimumHeight(100)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #666;
                border-radius: 5px;
                background-color: rgba(255, 255, 255, 0.05);
                font-size: 11pt;
            }
        """)
        file_layout.addWidget(self.drop_label)
        
        # File path input
        file_path_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText(self.tm('data_file_path'))
        self.file_path_input.setReadOnly(True)
        file_path_layout.addWidget(self.file_path_input)
        
        self.browse_button = QPushButton(self.tm('data_browse'))
        self.browse_button.clicked.connect(self.browse_file)
        file_path_layout.addWidget(self.browse_button)
        
        file_layout.addLayout(file_path_layout)
        
        # File parameters
        file_params_layout = QFormLayout()
        
        self.dt_file_spin = QDoubleSpinBox()
        self.dt_file_spin.setRange(0.001, 100.0)
        self.dt_file_spin.setValue(1.0)
        self.dt_file_spin.setDecimals(3)
        file_params_layout.addRow(self.tm('data_dt') + ':', self.dt_file_spin)
        
        file_layout.addLayout(file_params_layout)
        
        self.file_group.setLayout(file_layout)
        layout.addWidget(self.file_group)
        
        # Generate system group
        self.generate_group = QGroupBox(self.tm('data_generate'))
        generate_layout = QFormLayout()
        
        # System type selector
        self.system_combo = QComboBox()
        self.system_combo.addItem(self.tm('data_lorenz'), 'lorenz')
        self.system_combo.addItem(self.tm('data_rossler'), 'rossler')
        self.system_combo.addItem(self.tm('data_logistic'), 'logistic')
        self.system_combo.addItem('Hénon Map', 'henon')
        self.system_combo.addItem(self.tm('data_sine'), 'sine')
        self.system_combo.addItem(self.tm('data_noise'), 'noise')
        generate_layout.addRow(self.tm('data_system_type') + ':', self.system_combo)
        
        # Number of points
        self.n_points_spin = QSpinBox()
        self.n_points_spin.setRange(100, 100000)
        self.n_points_spin.setValue(5000)
        self.n_points_spin.setSingleStep(100)
        generate_layout.addRow(self.tm('data_points') + ':', self.n_points_spin)
        
        # Time step
        self.dt_gen_spin = QDoubleSpinBox()
        self.dt_gen_spin.setRange(0.001, 10.0)
        self.dt_gen_spin.setValue(0.01)
        self.dt_gen_spin.setDecimals(3)
        generate_layout.addRow(self.tm('data_dt') + ':', self.dt_gen_spin)
        
        self.generate_group.setLayout(generate_layout)
        layout.addWidget(self.generate_group)
        
        # Load button
        self.load_button = QPushButton(self.tm('data_load_button'))
        self.load_button.clicked.connect(self.load_data)
        self.load_button.setMinimumHeight(40)
        layout.addWidget(self.load_button)
        
        # Veri tablosu buraya eklenecek (content_panel tarafindan)
        self.table_placeholder = QVBoxLayout()
        layout.addLayout(self.table_placeholder)
        
        # Initial state
        self.on_source_changed()
    
    def set_table_widget(self, table_widget):
        """Veri tablosunu butonun hemen altina yerlestirir"""
        self.table_placeholder.addWidget(table_widget)
    
    def on_source_changed(self):
        """Handle source type change"""
        is_file = self.file_radio.isChecked()
        self.file_group.setVisible(is_file)
        self.generate_group.setVisible(not is_file)
    
    def browse_file(self):
        """Open file browser"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tm('data_load_file'),
            '',
            'Data Files (*.csv *.txt *.dat);;All Files (*.*)'
        )
        
        if file_path:
            self.file_path_input.setText(file_path)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #0e639c;
                    border-radius: 5px;
                    background-color: rgba(14, 99, 156, 0.2);
                    font-size: 11pt;
                }
            """)
    
    def dragLeaveEvent(self, event):
        """Handle drag leave"""
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #666;
                border-radius: 5px;
                background-color: rgba(255, 255, 255, 0.05);
                font-size: 11pt;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        """Handle file drop"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if os.path.isfile(file_path):
                self.file_path_input.setText(file_path)
                self.file_radio.setChecked(True)
                event.acceptProposedAction()
        
        # Reset style
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #666;
                border-radius: 5px;
                background-color: rgba(255, 255, 255, 0.05);
                font-size: 11pt;
            }
        """)
    
    def load_data(self):
        """Load data from file or generate"""
        try:
            if self.file_radio.isChecked():
                # Load from file
                file_path = self.file_path_input.text()
                if not file_path:
                    return
                
                from core.loaders import load_csv, load_txt
                
                # Determine file type
                ext = os.path.splitext(file_path)[1].lower()
                dt = self.dt_file_spin.value()
                
                if ext == '.csv':
                    ts = load_csv(file_path, dt=dt)
                else:
                    ts = load_txt(file_path, dt=dt)
                
                self.data_loaded.emit(ts)
                
            else:
                # Generate system
                system_type = self.system_combo.currentData()
                n_points = self.n_points_spin.value()
                dt = self.dt_gen_spin.value()
                
                from core.generators import (
                    generate_lorenz, generate_rossler, logistic_map, henon_map,
                    generate_sine, generate_white_noise
                )
                
                if system_type == 'lorenz':
                    ts = generate_lorenz(t_span=(0, n_points * dt), dt=dt)
                elif system_type == 'rossler':
                    ts = generate_rossler(t_span=(0, n_points * dt), dt=dt)
                elif system_type == 'logistic':
                    ts = logistic_map(n=n_points)
                elif system_type == 'henon':
                    ts = henon_map(n=n_points)
                elif system_type == 'sine':
                    ts = generate_sine(n=n_points, dt=dt)
                elif system_type == 'noise':
                    ts = generate_white_noise(n=n_points, dt=dt)
                
                self.data_loaded.emit(ts)
        
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def refresh_ui(self):
        """Refresh UI with current language"""
        self.file_radio.setText(self.tm('data_load_file'))
        self.generate_radio.setText(self.tm('data_generate'))
        self.file_group.setTitle(self.tm('data_load_file'))
        self.generate_group.setTitle(self.tm('data_generate'))
        self.browse_button.setText(self.tm('data_browse'))
        self.load_button.setText(self.tm('data_load_button'))
