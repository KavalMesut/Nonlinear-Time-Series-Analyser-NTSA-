"""
Linear analysis panel (ACF, PACF, FFT) — sadece kontroller, grafik PlotPanel'de.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGroupBox, QLabel, QSpinBox, QComboBox, QFormLayout,
    QProgressBar
)
from PySide6.QtCore import Qt, Signal, QThread
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
    """Linear analysis panel — sadece kontroller"""
    
    analysis_complete = Signal(dict)
    plot_requested = Signal(dict)   # grafik verisi PlotPanel'e gonderilir
    
    def __init__(self, translation_manager, theme_manager=None):
        super().__init__()
        self.tm = translation_manager
        self.theme_manager = theme_manager
        self.current_data = None
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        controls_group = QGroupBox(self.tm('analysis_acf'))
        controls_layout = QFormLayout()
        
        self.analysis_combo = QComboBox()
        self.analysis_combo.addItem(self.tm('analysis_acf'), 'acf')
        self.analysis_combo.addItem(self.tm('analysis_pacf'), 'pacf')
        self.analysis_combo.addItem(self.tm('analysis_fft'), 'fft')
        self.analysis_combo.currentIndexChanged.connect(self.on_analysis_changed)
        controls_layout.addRow(QLabel("Analysis:"), self.analysis_combo)
        
        self.max_lag_spin = QSpinBox()
        self.max_lag_spin.setRange(10, 1000)
        self.max_lag_spin.setValue(100)
        controls_layout.addRow(QLabel("Max Lag:"), self.max_lag_spin)
        
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
        
        self.calc_button = QPushButton(self.tm('btn_calculate'))
        self.calc_button.clicked.connect(self.calculate)
        self.calc_button.setEnabled(False)
        layout.addWidget(self.calc_button)
        
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        layout.addStretch()
    
    def set_data(self, timeseries):
        self.current_data = timeseries
        self.calc_button.setEnabled(True)
    
    def on_analysis_changed(self):
        analysis_type = self.analysis_combo.currentData()
        is_fft = (analysis_type == 'fft')
        self.max_lag_spin.setVisible(not is_fft)
        self.window_combo.setVisible(is_fft)
        self.window_label.setVisible(is_fft)
    
    def calculate(self):
        if self.current_data is None:
            return
        
        analysis_type = self.analysis_combo.currentData()
        params = {
            'max_lag': self.max_lag_spin.value(),
            'dt': self.current_data.dt,
            'window': self.window_combo.currentData()
        }
        
        self.worker = AnalysisWorker(self.current_data.data, analysis_type, params)
        self.worker.finished.connect(self.on_analysis_complete)
        self.worker.error.connect(self.on_analysis_error)
        
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.calc_button.setEnabled(False)
        self.worker.start()
    
    def on_analysis_complete(self, results):
        self.progress.setVisible(False)
        self.calc_button.setEnabled(True)
        
        analysis_type = self.analysis_combo.currentData()
        n = len(self.current_data.data) if self.current_data else 1000
        
        # PlotPanel'e grafik verisi gonder
        self.plot_requested.emit({
            'type': 'linear',
            'analysis_type': analysis_type,
            'results': results,
            'n_data': n
        })
        
        self.analysis_complete.emit(results)
    
    def on_analysis_error(self, error_msg):
        self.progress.setVisible(False)
        self.calc_button.setEnabled(True)
        print(f"Analysis error: {error_msg}")
    
    def refresh_ui(self):
        self.calc_button.setText(self.tm('btn_calculate'))
