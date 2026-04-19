"""
Parameter estimation panel (AMI for tau, FNN for m)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGroupBox, QLabel, QSpinBox, QFormLayout,
    QProgressBar, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QThread
import pyqtgraph as pg
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
        """Run parameter estimation"""
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
    """Parameter estimation panel"""
    
    parameters_estimated = Signal(dict)
    
    def __init__(self, translation_manager, theme_manager):
        super().__init__()
        self.tm = translation_manager
        self.theme_manager = theme_manager
        self.current_data = None
        self.tau = None
        self.m = None
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
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
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self.update_plot_theme()
        self.plot_widget.setLabel('left', 'AMI')
        self.plot_widget.setLabel('bottom', 'Lag')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.plot_widget)
    
    def set_data(self, timeseries):
        """Set data for parameter estimation"""
        self.current_data = timeseries
        self.estimate_tau_button.setEnabled(True)
    
    def estimate_tau(self):
        """Estimate tau using AMI"""
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
        """Estimate m using FNN"""
        if self.current_data is None or self.tau is None:
            return
        
        params = {
            'tau': self.tau,
            'max_dim': self.m_max_dim_spin.value()
        }
        
        self.worker = ParameterWorker(self.current_data.data, 'm', params)
        self.worker.finished.connect(self.on_m_estimated)
        self.worker.error.connect(self.on_error)
        
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.estimate_m_button.setEnabled(False)
        
        self.worker.start()
    
    def on_tau_estimated(self, results):
        """Handle tau estimation completion"""
        self.progress.setVisible(False)
        self.estimate_tau_button.setEnabled(True)
        
        self.tau = results['tau']
        self.tau_result_label.setText(f"τ = {self.tau}")
        
        # Plot AMI
        self.plot_widget.clear()
        self.plot_widget.setLabel('left', 'AMI')
        self.plot_widget.setLabel('bottom', 'Lag')
        self.plot_widget.plot(results['lags'], results['ami'],
                            pen=pg.mkPen(color='#268bd2', width=2))
        
        # Mark first minimum
        ami_values = results['ami']
        self.plot_widget.plot([self.tau], [ami_values[self.tau-1]],
                            pen=None, symbol='o', symbolSize=10,
                            symbolBrush='red')
        
        # Enable m estimation
        self.estimate_m_button.setEnabled(True)
        
        self.parameters_estimated.emit({'tau': self.tau})
    
    def on_m_estimated(self, results):
        """Handle m estimation completion"""
        self.progress.setVisible(False)
        self.estimate_m_button.setEnabled(True)
        
        self.m = results['m']
        self.m_result_label.setText(f"m = {self.m}")
        
        # Plot FNN
        self.plot_widget.clear()
        self.plot_widget.setLabel('left', 'FNN %')
        self.plot_widget.setLabel('bottom', 'Dimension')
        self.plot_widget.plot(results['dimensions'], results['fnn'],
                            pen=pg.mkPen(color='#859900', width=2))
        
        # Mark threshold
        self.plot_widget.plot(results['dimensions'], [1.0] * len(results['dimensions']),
                            pen=pg.mkPen(color='red', style=Qt.DashLine))
        
        self.parameters_estimated.emit({'tau': self.tau, 'm': self.m})
    
    def on_error(self, error_msg):
        """Handle error"""
        self.progress.setVisible(False)
        self.estimate_tau_button.setEnabled(True)
        self.estimate_m_button.setEnabled(True)
        print(f"Parameter estimation error: {error_msg}")
    
    def update_plot_theme(self):
        """Update plot theme"""
        theme = self.theme_manager.get_theme()
        self.plot_widget.setBackground(theme.colors['plot_bg'])
        
        for axis in ['left', 'bottom', 'right', 'top']:
            ax = self.plot_widget.getAxis(axis)
            ax.setPen(pg.mkPen(color=theme.colors['plot_text'], width=1))
            ax.setTextPen(pg.mkPen(color=theme.colors['plot_text']))
    
    def get_parameters(self):
        """Get estimated parameters"""
        return {'tau': self.tau, 'm': self.m}
    
    def refresh_ui(self):
        """Refresh UI with current language"""
        self.estimate_tau_button.setText(self.tm('btn_calculate') + ' τ')
        self.estimate_m_button.setText(self.tm('btn_calculate') + ' m')
