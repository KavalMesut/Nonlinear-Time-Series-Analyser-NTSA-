"""
Linear analysis panel (ACF, PACF, FFT)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGroupBox, QLabel, QSpinBox, QComboBox, QFormLayout,
    QProgressBar
)
from PySide6.QtCore import Qt, Signal, QThread
import pyqtgraph as pg
import numpy as np


class AnalysisWorker(QThread):
    """Worker thread for analysis"""
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, data, analysis_type, params):
        super().__init__()
        self.data = data
        self.analysis_type = analysis_type
        self.params = params
    
    def run(self):
        """Run analysis"""
        try:
            from analysis import compute_acf, compute_pacf, compute_fft
            
            results = {}
            
            if self.analysis_type == 'acf':
                results['acf'] = compute_acf(self.data, max_lag=self.params.get('max_lag', 100))
                results['lags'] = np.arange(len(results['acf']))
            
            elif self.analysis_type == 'pacf':
                results['pacf'] = compute_pacf(self.data, max_lag=self.params.get('max_lag', 50))
                results['lags'] = np.arange(len(results['pacf']))
            
            elif self.analysis_type == 'fft':
                freqs, power = compute_fft(self.data, dt=self.params.get('dt', 1.0), 
                                          window=self.params.get('window', 'hann'))
                results['frequencies'] = freqs
                results['power'] = power
            
            self.finished.emit(results)
        
        except Exception as e:
            self.error.emit(str(e))


class LinearAnalysisPanel(QWidget):
    """Linear analysis panel"""
    
    analysis_complete = Signal(dict)
    
    def __init__(self, translation_manager, theme_manager):
        super().__init__()
        self.tm = translation_manager
        self.theme_manager = theme_manager
        self.current_data = None
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Controls
        controls_group = QGroupBox(self.tm('analysis_acf'))
        controls_layout = QFormLayout()
        
        # Analysis type
        self.analysis_combo = QComboBox()
        self.analysis_combo.addItem(self.tm('analysis_acf'), 'acf')
        self.analysis_combo.addItem(self.tm('analysis_pacf'), 'pacf')
        self.analysis_combo.addItem(self.tm('analysis_fft'), 'fft')
        self.analysis_combo.currentIndexChanged.connect(self.on_analysis_changed)
        controls_layout.addRow(QLabel("Analysis:"), self.analysis_combo)
        
        # Max lag (for ACF/PACF)
        self.max_lag_spin = QSpinBox()
        self.max_lag_spin.setRange(10, 1000)
        self.max_lag_spin.setValue(100)
        controls_layout.addRow(QLabel("Max Lag:"), self.max_lag_spin)
        
        # Window type (for FFT)
        self.window_combo = QComboBox()
        self.window_combo.addItem("Hann", "hann")
        self.window_combo.addItem("Hamming", "hamming")
        self.window_combo.addItem("Blackman", "blackman")
        self.window_combo.addItem("None", "none")
        self.window_combo.setVisible(False)
        self.window_label = QLabel("Window:")
        self.window_label.setVisible(False)
        controls_layout.addRow(self.window_label, self.window_combo)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Calculate button
        self.calc_button = QPushButton(self.tm('btn_calculate'))
        self.calc_button.clicked.connect(self.calculate)
        self.calc_button.setEnabled(False)
        layout.addWidget(self.calc_button)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self.update_plot_theme()
        self.plot_widget.setLabel('left', 'Value')
        self.plot_widget.setLabel('bottom', 'Lag')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.plot_widget)
    
    def set_data(self, timeseries):
        """Set data for analysis"""
        self.current_data = timeseries
        self.calc_button.setEnabled(True)
    
    def on_analysis_changed(self):
        """Handle analysis type change"""
        analysis_type = self.analysis_combo.currentData()
        
        # Show/hide controls based on analysis type
        is_fft = (analysis_type == 'fft')
        self.max_lag_spin.setVisible(not is_fft)
        self.window_combo.setVisible(is_fft)
        self.window_label.setVisible(is_fft)
        
        # Update plot labels
        if analysis_type == 'acf':
            self.plot_widget.setLabel('left', 'ACF')
            self.plot_widget.setLabel('bottom', 'Lag')
        elif analysis_type == 'pacf':
            self.plot_widget.setLabel('left', 'PACF')
            self.plot_widget.setLabel('bottom', 'Lag')
        elif analysis_type == 'fft':
            self.plot_widget.setLabel('left', 'Power')
            self.plot_widget.setLabel('bottom', 'Frequency (Hz)')
    
    def calculate(self):
        """Start analysis"""
        if self.current_data is None:
            return
        
        analysis_type = self.analysis_combo.currentData()
        
        params = {
            'max_lag': self.max_lag_spin.value(),
            'dt': self.current_data.dt,
            'window': self.window_combo.currentData()
        }
        
        # Start worker thread
        self.worker = AnalysisWorker(self.current_data.data, analysis_type, params)
        self.worker.finished.connect(self.on_analysis_complete)
        self.worker.error.connect(self.on_analysis_error)
        
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # Indeterminate
        self.calc_button.setEnabled(False)
        
        self.worker.start()
    
    def on_analysis_complete(self, results):
        """Handle analysis completion"""
        self.progress.setVisible(False)
        self.calc_button.setEnabled(True)
        
        # Plot results
        self.plot_widget.clear()
        analysis_type = self.analysis_combo.currentData()
        
        if analysis_type == 'acf':
            self.plot_widget.plot(results['lags'], results['acf'], 
                                pen=pg.mkPen(color='#0e639c', width=2))
            # Add significance lines
            n = len(self.current_data.data)
            conf = 1.96 / np.sqrt(n)
            self.plot_widget.plot(results['lags'], [conf] * len(results['lags']),
                                pen=pg.mkPen(color='red', style=Qt.DashLine))
            self.plot_widget.plot(results['lags'], [-conf] * len(results['lags']),
                                pen=pg.mkPen(color='red', style=Qt.DashLine))
        
        elif analysis_type == 'pacf':
            self.plot_widget.plot(results['lags'], results['pacf'],
                                pen=pg.mkPen(color='#859900', width=2))
        
        elif analysis_type == 'fft':
            self.plot_widget.plot(results['frequencies'], results['power'],
                                pen=pg.mkPen(color='#d33682', width=1.5))
            self.plot_widget.setLogMode(y=True)
        
        self.analysis_complete.emit(results)
    
    def on_analysis_error(self, error_msg):
        """Handle analysis error"""
        self.progress.setVisible(False)
        self.calc_button.setEnabled(True)
        print(f"Analysis error: {error_msg}")
    
    def update_plot_theme(self):
        """Update plot theme"""
        theme = self.theme_manager.get_theme()
        self.plot_widget.setBackground(theme.colors['plot_bg'])
        
        for axis in ['left', 'bottom', 'right', 'top']:
            ax = self.plot_widget.getAxis(axis)
            ax.setPen(pg.mkPen(color=theme.colors['plot_text'], width=1))
            ax.setTextPen(pg.mkPen(color=theme.colors['plot_text']))
    
    def refresh_ui(self):
        """Refresh UI with current language"""
        self.calc_button.setText(self.tm('btn_calculate'))
