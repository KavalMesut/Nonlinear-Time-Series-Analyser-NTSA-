"""
Chaos analysis panel (Lyapunov, Correlation Dimension, Lyapunov Spectrum)
Sadece kontroller — grafik PlotPanel'de gosterilir.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGroupBox, QLabel, QSpinBox, QDoubleSpinBox,
    QFormLayout, QProgressBar, QTextEdit, QComboBox
)
from PySide6.QtCore import Qt, Signal, QThread
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
        try:
            from analysis import (
                lyapunov_wolf, lyapunov_rosenstein,
                estimate_lyapunov_from_curve, correlation_dimension,
                lyapunov_spectrum
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
                    fit_end = min(30, len(t_steps))
                    lyap = estimate_lyapunov_from_curve(t_steps, divergence, fit_start=0, fit_end=fit_end)
                    results['lyapunov'] = lyap
                    results['t_steps'] = t_steps
                    results['divergence'] = divergence
                    results['algorithm'] = 'Rosenstein'
            
            elif self.analysis_type == 'spectrum':
                self.progress.emit("Calculating full Lyapunov spectrum (Benettin)...")
                spec = lyapunov_spectrum(self.data, m=self.m, tau=self.tau, dt=self.dt)
                results['spectrum'] = spec
            
            elif self.analysis_type == 'correlation_dim':
                self.progress.emit("Calculating correlation dimension...")
                radii, c_r = correlation_dimension(self.data, m=self.m, tau=self.tau, n_radii=30)
                from analysis import estimate_dimension_from_correlation
                valid = c_r > 0
                if np.sum(valid) > 2:
                    dim = estimate_dimension_from_correlation(radii, c_r, fit_start=5, fit_end=20)
                    results['dimension'] = dim
                else:
                    results['dimension'] = np.nan
                results['radii'] = radii
                results['c_r'] = c_r
            
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class ChaosAnalysisPanel(QWidget):
    """Chaos analysis panel — sadece kontroller"""
    
    analysis_complete = Signal(dict)
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
        
        # Parameters
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
        
        # Lyapunov Spectrum
        spec_group = QGroupBox("Lyapunov Spectrum")
        spec_layout = QVBoxLayout()
        
        self.calc_spec_button = QPushButton("Calculate Full Spectrum")
        self.calc_spec_button.clicked.connect(self.calculate_spectrum)
        self.calc_spec_button.setEnabled(False)
        spec_layout.addWidget(self.calc_spec_button)
        
        self.spec_result_label = QLabel("λ₁, λ₂, ... = ?")
        self.spec_result_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #b58900;")
        self.spec_result_label.setWordWrap(True)
        spec_layout.addWidget(self.spec_result_label)
        
        self.spec_info = QTextEdit()
        self.spec_info.setReadOnly(True)
        self.spec_info.setMaximumHeight(120)
        spec_layout.addWidget(self.spec_info)
        
        spec_group.setLayout(spec_layout)
        layout.addWidget(spec_group)
        
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
        
        layout.addStretch()
    
    def set_data(self, timeseries, tau, m):
        self.current_data = timeseries
        self.tau = tau
        self.m = m
        self.tau_label.setText(f"τ = {tau}")
        self.m_label.setText(f"m = {m}")
        self.calc_lyap_button.setEnabled(True)
        self.calc_corr_button.setEnabled(True)
        self.calc_spec_button.setEnabled(True)
    
    def calculate_lyapunov(self):
        if not self._check_ready():
            return
        algo = self.algo_combo.currentData()
        self.worker = ChaosWorker(
            self.current_data.data, self.tau, self.m,
            'lyapunov', algorithm=algo, dt=self.current_data.dt
        )
        self.worker.finished.connect(self.on_lyapunov_complete)
        self.worker.error.connect(self.on_error)
        self.worker.progress.connect(self.on_progress)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.calc_lyap_button.setEnabled(False)
        self.worker.start()
    
    def calculate_spectrum(self):
        if not self._check_ready():
            return
        self.worker = ChaosWorker(
            self.current_data.data, self.tau, self.m,
            'spectrum', dt=self.current_data.dt
        )
        self.worker.finished.connect(self.on_spectrum_complete)
        self.worker.error.connect(self.on_error)
        self.worker.progress.connect(self.on_progress)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.calc_spec_button.setEnabled(False)
        self.worker.start()
    
    def calculate_correlation_dim(self):
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
        self.progress.setVisible(False)
        self.calc_lyap_button.setEnabled(True)
        self.status_label.setText("")
        
        lyap = results['lyapunov']
        algo_name = results.get('algorithm', 'Unknown')
        self.lyap_result_label.setText(f"λ₁ = {lyap:.4f}")
        
        info = f"Algorithm: {algo_name}\n"
        info += f"Largest Lyapunov Exponent: {lyap:.4f}\n\n"
        if np.isnan(lyap):
            info += "Calculation failed or insufficient divergence.\n"
        elif lyap > 0.1:
            info += "Positive Lyapunov exponent - CHAOTIC behavior\n"
        elif lyap > 0:
            info += "Small positive exponent - Weak chaos\n"
        elif abs(lyap) < 0.01:
            info += "Near zero - Periodic or quasi-periodic\n"
        else:
            info += "Negative exponent - Stable/damped system\n"
        self.lyap_info.setText(info)
        
        self.plot_requested.emit({
            'type': 'chaos_lyapunov',
            'results': results
        })
        self.analysis_complete.emit(results)
    
    def on_spectrum_complete(self, results):
        self.progress.setVisible(False)
        self.calc_spec_button.setEnabled(True)
        self.status_label.setText("")
        
        spec = results.get('spectrum', {})
        exponents = spec.get('exponents', np.array([]))
        ky_dim = spec.get('kaplan_yorke_dim', np.nan)
        ks_ent = spec.get('kolmogorov_sinai', np.nan)
        n_steps = spec.get('n_steps', 0)
        
        if len(exponents) == 0:
            self.spec_result_label.setText("Spectrum calculation failed")
            return
        
        exp_strs = [f"λ{i+1}={e:.4f}" for i, e in enumerate(exponents)]
        self.spec_result_label.setText("  ".join(exp_strs))
        
        info = f"Full Lyapunov Spectrum (Benettin/QR method)\n"
        info += f"Embedding dimension: m={self.m}, Steps used: {n_steps}\n"
        info += f"Kaplan-Yorke Dimension: D_KY = {ky_dim:.4f}\n"
        info += f"Kolmogorov-Sinai Entropy: h_KS = {ks_ent:.4f} nats/s\n\n"
        n_pos = int(np.sum(exponents > 0))
        n_zero = int(np.sum(np.abs(exponents) < 0.01))
        n_neg = int(np.sum(exponents < -0.01))
        info += f"Positive: {n_pos}, Near-zero: {n_zero}, Negative: {n_neg}\n"
        if n_pos > 0:
            info += "System exhibits CHAOTIC behavior"
        elif n_zero > 0:
            info += "System may be quasi-periodic"
        else:
            info += "System appears STABLE (all exponents negative)"
        self.spec_info.setText(info)
        
        self.plot_requested.emit({
            'type': 'chaos_spectrum',
            'exponents': exponents
        })
        self.analysis_complete.emit(results)
    
    def on_correlation_complete(self, results):
        self.progress.setVisible(False)
        self.calc_corr_button.setEnabled(True)
        self.status_label.setText("")
        
        dim = results['dimension']
        self.corr_result_label.setText(f"D₂ = {dim:.4f}")
        
        self.plot_requested.emit({
            'type': 'chaos_correlation',
            'results': results
        })
        self.analysis_complete.emit(results)
    
    def on_progress(self, message):
        self.status_label.setText(message)
    
    def on_error(self, error_msg):
        self.progress.setVisible(False)
        self.calc_lyap_button.setEnabled(True)
        self.calc_corr_button.setEnabled(True)
        self.calc_spec_button.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")
    
    def _check_ready(self):
        return (self.current_data is not None and
                self.tau is not None and
                self.m is not None)
    
    def refresh_ui(self):
        self.calc_lyap_button.setText(self.tm('btn_calculate') + ' Lyapunov')
        self.calc_corr_button.setText(self.tm('btn_calculate') + ' Correlation Dim')
