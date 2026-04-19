"""
Chaos analysis panel (Lyapunov, Correlation Dimension)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGroupBox, QLabel, QSpinBox, QDoubleSpinBox,
    QFormLayout, QProgressBar, QTextEdit, QComboBox
)
from PySide6.QtCore import Qt, Signal, QThread
import pyqtgraph as pg
import numpy as np


class ChaosWorker(QThread):
    """Worker thread for chaos analysis"""
    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(str)
    
    def __init__(self, data, tau, m, analysis_type, algorithm='wolf', dt=1.0):
        super().__init__()
        self.data = data
        self.tau = tau
        self.m = m
        self.analysis_type = analysis_type
        self.algorithm = algorithm
        self.dt = dt
    
    def run(self):
        """Run chaos analysis"""
        try:
            from analysis import (
                lyapunov_wolf, lyapunov_rosenstein, 
                estimate_lyapunov_from_curve, correlation_dimension
            )
            
            results = {}
            
            if self.analysis_type == 'lyapunov':
                if self.algorithm == 'wolf':
                    self.progress.emit("Calculating Lyapunov exponent (Wolf algorithm)...")
                    lyap = lyapunov_wolf(self.data, m=self.m, tau=self.tau, dt=self.dt)
                    results['lyapunov'] = lyap
                    results['algorithm'] = 'Wolf'
                else:
                    self.progress.emit("Calculating Lyapunov exponent (Rosenstein algorithm)...")
                    t_steps, divergence = lyapunov_rosenstein(self.data, m=self.m, tau=self.tau, dt=self.dt)
                    
                    # Estimate dimension from curve (initial linear part)
                    fit_end = min(30, len(t_steps))
                    lyap = estimate_lyapunov_from_curve(t_steps, divergence, fit_start=0, fit_end=fit_end)
                    
                    results['lyapunov'] = lyap
                    results['t_steps'] = t_steps
                    results['divergence'] = divergence
                    results['algorithm'] = 'Rosenstein'
            
            elif self.analysis_type == 'correlation_dim':
                self.progress.emit("Calculating correlation dimension...")
                radii, c_r = correlation_dimension(self.data, m=self.m, tau=self.tau, n_radii=30)
                
                # Estimate dimension
                from analysis import estimate_dimension_from_correlation
                valid = c_r > 0
                if np.sum(valid) > 2:
                    dim = estimate_dimension_from_correlation(radii, c_r, 
                                                             fit_start=5, fit_end=20)
                    results['dimension'] = dim
                else:
                    results['dimension'] = np.nan
                
                results['radii'] = radii
                results['c_r'] = c_r
            
            self.finished.emit(results)
        
        except Exception as e:
            self.error.emit(str(e))


class ChaosAnalysisPanel(QWidget):
    """Chaos analysis panel"""
    
    analysis_complete = Signal(dict)
    
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
        
        # Parameters display
        params_group = QGroupBox("Parameters")
        params_layout = QFormLayout()
        self.tau_label = QLabel("τ = ?")
        self.m_label = QLabel("m = ?")
        params_layout.addRow("Time Delay:", self.tau_label)
        params_layout.addRow("Embedding Dimension:", self.m_label)
        
        self.algo_combo = QComboBox()
        self.algo_combo.addItem("Wolf Algorithm", "wolf")
        self.algo_combo.addItem("Rosenstein Algorithm", "rosenstein")
        params_layout.addRow("Algorithm:", self.algo_combo)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Lyapunov exponent
        lyap_group = QGroupBox(self.tm('analysis_lyapunov'))
        lyap_layout = QVBoxLayout()
        
        self.calc_lyap_button = QPushButton(self.tm('btn_calculate') + ' Lyapunov')
        self.calc_lyap_button.clicked.connect(self.calculate_lyapunov)
        self.calc_lyap_button.setEnabled(False)
        lyap_layout.addWidget(self.calc_lyap_button)
        
        self.lyap_result_label = QLabel("λ = ?")
        self.lyap_result_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #0e639c;")
        lyap_layout.addWidget(self.lyap_result_label)
        
        self.lyap_info = QTextEdit()
        self.lyap_info.setReadOnly(True)
        self.lyap_info.setMaximumHeight(100)
        lyap_layout.addWidget(self.lyap_info)
        
        lyap_group.setLayout(lyap_layout)
        layout.addWidget(lyap_group)
        
        # Correlation dimension
        corr_group = QGroupBox(self.tm('analysis_correlation_dim'))
        corr_layout = QVBoxLayout()
        
        self.calc_corr_button = QPushButton(self.tm('btn_calculate') + ' Correlation Dim')
        self.calc_corr_button.clicked.connect(self.calculate_correlation_dim)
        self.calc_corr_button.setEnabled(False)
        corr_layout.addWidget(self.calc_corr_button)
        
        self.corr_result_label = QLabel("D₂ = ?")
        self.corr_result_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #859900;")
        corr_layout.addWidget(self.corr_result_label)
        
        corr_group.setLayout(corr_layout)
        layout.addWidget(corr_group)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self.update_plot_theme()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.plot_widget)
    
    def set_data(self, timeseries, tau, m):
        """Set data and parameters"""
        self.current_data = timeseries
        self.tau = tau
        self.m = m
        
        self.tau_label.setText(f"τ = {tau}")
        self.m_label.setText(f"m = {m}")
        
        self.calc_lyap_button.setEnabled(True)
        self.calc_corr_button.setEnabled(True)
    
    def calculate_lyapunov(self):
        """Calculate Lyapunov exponent"""
        if not self._check_ready():
            return
        
        algo = self.algo_combo.currentData()
        
        self.worker = ChaosWorker(
            self.current_data.data,
            self.tau,
            self.m,
            'lyapunov',
            algorithm=algo,
            dt=self.current_data.dt,
        )
        self.worker.finished.connect(self.on_lyapunov_complete)
        self.worker.error.connect(self.on_error)
        self.worker.progress.connect(self.on_progress)
        
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.calc_lyap_button.setEnabled(False)
        
        self.worker.start()
    
    def calculate_correlation_dim(self):
        """Calculate correlation dimension"""
        if not self._check_ready():
            return
        
        self.worker = ChaosWorker(self.current_data.data, self.tau, self.m, 'correlation_dim')
        self.worker.finished.connect(self.on_correlation_complete)
        self.worker.error.connect(self.on_error)
        self.worker.progress.connect(self.on_progress)
        
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.calc_corr_button.setEnabled(False)
        
        self.worker.start()
    
    def on_lyapunov_complete(self, results):
        """Handle Lyapunov calculation completion"""
        self.progress.setVisible(False)
        self.calc_lyap_button.setEnabled(True)
        self.status_label.setText("")
        
        lyap = results['lyapunov']
        algo_name = results.get('algorithm', 'Unknown')
        self.lyap_result_label.setText(f"λ₁ = {lyap:.4f}")
        
        # Interpretation
        info = f"Algorithm: {algo_name}\n"
        info += f"Largest Lyapunov Exponent: {lyap:.4f}\n\n"
        
        if np.isnan(lyap):
            info += "✗ Calculation failed or insufficient divergence.\n"
        elif lyap > 0.1:
            info += "✓ Positive Lyapunov exponent - CHAOTIC behavior\n"
        elif lyap > 0:
            info += "⚠ Small positive exponent - Weak chaos\n"
        elif abs(lyap) < 0.01:
            info += "≈ Near zero - Periodic or quasi-periodic\n"
        else:
            info += "✗ Negative exponent - Stable/damped system\n"
        
        self.lyap_info.setText(info)
        
        # Update plot if Rosenstein results are available
        self.plot_widget.clear()
        if 't_steps' in results and 'divergence' in results:
            self.plot_widget.setLabel('left', 'ln(divergence)')
            self.plot_widget.setLabel('bottom', 'Time')
            
            t = results['t_steps']
            d = results['divergence']
            valid = ~np.isnan(d)
            self.plot_widget.plot(t[valid], d[valid], pen=pg.mkPen(color='#0e639c', width=2))
        
        self.analysis_complete.emit(results)

    
    def on_correlation_complete(self, results):
        """Handle correlation dimension completion"""
        self.progress.setVisible(False)
        self.calc_corr_button.setEnabled(True)
        self.status_label.setText("")
        
        dim = results['dimension']
        self.corr_result_label.setText(f"D₂ = {dim:.4f}")
        
        # Plot log-log correlation sum
        self.plot_widget.clear()
        self.plot_widget.setLabel('left', 'log(C(r))')
        self.plot_widget.setLabel('bottom', 'log(r)')
        
        radii = results['radii']
        c_r = results['c_r']
        
        valid = c_r > 0
        if np.any(valid):
            log_r = np.log(radii[valid])
            log_c = np.log(c_r[valid])
            self.plot_widget.plot(log_r, log_c,
                                pen=pg.mkPen(color='#859900', width=2),
                                symbol='o', symbolSize=5)
        
        self.analysis_complete.emit(results)
    
    def on_progress(self, message):
        """Handle progress update"""
        self.status_label.setText(message)
    
    def on_error(self, error_msg):
        """Handle error"""
        self.progress.setVisible(False)
        self.calc_lyap_button.setEnabled(True)
        self.calc_corr_button.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")
    
    def _check_ready(self):
        """Check if ready for analysis"""
        return (self.current_data is not None and 
                self.tau is not None and 
                self.m is not None)
    
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
        self.calc_lyap_button.setText(self.tm('btn_calculate') + ' Lyapunov')
        self.calc_corr_button.setText(self.tm('btn_calculate') + ' Correlation Dim')
