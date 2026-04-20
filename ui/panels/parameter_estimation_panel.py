"""
Parameter estimation panel (AMI for tau, FNN for m) — sadece kontroller, grafik PlotPanel'de.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGroupBox, QLabel, QSpinBox, QFormLayout,
    QProgressBar
)
from PySide6.QtCore import Qt, Signal, QThread
import numpy as np


class ParameterWorker(QThread):
    """Worker thread for parameter estimation"""
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, data, estimation_type, params):
        super().__init__()
        self.data = data
        self.estimation_type = estimation_type
        self.params = params
    
    def run(self):
        try:
            from analysis import (
                compute_ami, find_first_minimum,
                compute_fnn, find_embedding_dimension
            )
            
            results = {}
            
            if self.estimation_type == 'tau':
                max_lag = self.params.get('max_lag', 100)
                ami = compute_ami(self.data, max_lag=max_lag)
                tau = find_first_minimum(ami)
                results['ami'] = ami
                results['lags'] = np.arange(1, len(ami) + 1)
                results['tau'] = tau
            
            elif self.estimation_type == 'm':
                tau = self.params.get('tau', 1)
                max_dim = self.params.get('max_dim', 10)
                fnn = compute_fnn(self.data, tau=tau, max_dim=max_dim)
                m = find_embedding_dimension(fnn, threshold=1.0)
                results['fnn'] = fnn
                results['dimensions'] = np.arange(1, len(fnn) + 1)
                results['m'] = m
            
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class ParameterEstimationPanel(QWidget):
    """Parameter estimation panel — sadece kontroller"""
    
    parameters_estimated = Signal(dict)
    plot_requested = Signal(dict)
    
    def __init__(self, translation_manager, theme_manager=None):
        super().__init__()
        self.tm = translation_manager
        self.theme_manager = theme_manager
        self.current_data = None
        self.tau = None
        self.m = None
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Tau estimation
        tau_group = QGroupBox(self.tm('param_tau') + ' - AMI')
        tau_layout = QVBoxLayout()
        
        tau_controls = QFormLayout()
        self.tau_max_lag_spin = QSpinBox()
        self.tau_max_lag_spin.setRange(10, 500)
        self.tau_max_lag_spin.setValue(100)
        tau_controls.addRow(QLabel("Max Lag:"), self.tau_max_lag_spin)
        tau_layout.addLayout(tau_controls)
        
        self.estimate_tau_button = QPushButton(self.tm('btn_calculate') + ' τ')
        self.estimate_tau_button.clicked.connect(self.estimate_tau)
        self.estimate_tau_button.setEnabled(False)
        tau_layout.addWidget(self.estimate_tau_button)
        
        self.tau_result_label = QLabel("τ = ?")
        self.tau_result_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        tau_layout.addWidget(self.tau_result_label)
        
        tau_group.setLayout(tau_layout)
        layout.addWidget(tau_group)
        
        # M estimation
        m_group = QGroupBox(self.tm('param_m') + ' - FNN')
        m_layout = QVBoxLayout()
        
        m_controls = QFormLayout()
        self.m_max_dim_spin = QSpinBox()
        self.m_max_dim_spin.setRange(2, 20)
        self.m_max_dim_spin.setValue(10)
        m_controls.addRow(QLabel("Max Dimension:"), self.m_max_dim_spin)
        m_layout.addLayout(m_controls)
        
        self.estimate_m_button = QPushButton(self.tm('btn_calculate') + ' m')
        self.estimate_m_button.clicked.connect(self.estimate_m)
        self.estimate_m_button.setEnabled(False)
        m_layout.addWidget(self.estimate_m_button)
        
        self.m_result_label = QLabel("m = ?")
        self.m_result_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        m_layout.addWidget(self.m_result_label)
        
        m_group.setLayout(m_layout)
        layout.addWidget(m_group)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        layout.addStretch()
    
    def set_data(self, timeseries):
        self.current_data = timeseries
        self.tau = None
        self.m = None
        self.tau_result_label.setText("τ = ?")
        self.m_result_label.setText("m = ?")
        self.estimate_tau_button.setEnabled(True)
        self.estimate_m_button.setEnabled(False)
    
    def estimate_tau(self):
        if self.current_data is None:
            return
        params = {'max_lag': self.tau_max_lag_spin.value()}
        self.worker = ParameterWorker(self.current_data.data, 'tau', params)
        self.worker.finished.connect(self.on_tau_estimated)
        self.worker.error.connect(self.on_error)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.estimate_tau_button.setEnabled(False)
        self.worker.start()
    
    def estimate_m(self):
        if self.current_data is None or self.tau is None:
            return
        params = {'tau': self.tau, 'max_dim': self.m_max_dim_spin.value()}
        self.worker = ParameterWorker(self.current_data.data, 'm', params)
        self.worker.finished.connect(self.on_m_estimated)
        self.worker.error.connect(self.on_error)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.estimate_m_button.setEnabled(False)
        self.worker.start()
    
    def on_tau_estimated(self, results):
        self.progress.setVisible(False)
        self.estimate_tau_button.setEnabled(True)
        self.tau = results['tau']
        self.tau_result_label.setText(f"τ = {self.tau}")
        self.estimate_m_button.setEnabled(True)
        
        self.plot_requested.emit({
            'type': 'param_tau',
            'results': results
        })
        
        self.parameters_estimated.emit({'tau': self.tau})
    
    def on_m_estimated(self, results):
        self.progress.setVisible(False)
        self.estimate_m_button.setEnabled(True)
        self.m = results['m']
        self.m_result_label.setText(f"m = {self.m}")
        
        self.plot_requested.emit({
            'type': 'param_m',
            'results': results
        })
        
        self.parameters_estimated.emit({'tau': self.tau, 'm': self.m})
    
    def on_error(self, error_msg):
        self.progress.setVisible(False)
        self.estimate_tau_button.setEnabled(True)
        self.estimate_m_button.setEnabled(True)
        print(f"Parameter estimation error: {error_msg}")
    
    def get_parameters(self):
        return {'tau': self.tau, 'm': self.m}
    
    def refresh_ui(self):
        self.estimate_tau_button.setText(self.tm('btn_calculate') + ' τ')
        self.estimate_m_button.setText(self.tm('btn_calculate') + ' m')
