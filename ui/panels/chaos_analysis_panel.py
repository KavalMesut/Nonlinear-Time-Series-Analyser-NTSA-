"""
Chaos analysis panel (Lyapunov, Correlation Dimension, Lyapunov Spectrum)
Sadece kontroller — grafik PlotPanel'de gosterilir.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGroupBox, QLabel, QSpinBox, QDoubleSpinBox,
    QFormLayout, QProgressBar, QTextEdit, QComboBox, QScrollArea, QSlider
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
import numpy as np


class ChaosWorker(QThread):
    """Worker thread for chaos analysis"""
    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, data, tau, m, analysis_type, algorithm='wolf', dt=1.0,
                 poincare_plane=None, poincare_direction=1):
        super().__init__()
        self.data = data
        self.tau = tau
        self.m = m
        self.analysis_type = analysis_type
        self.algorithm = algorithm
        self.dt = dt
        self.poincare_plane = poincare_plane
        self.poincare_direction = poincare_direction

    def run(self):
        try:
            from analysis import (
                lyapunov_wolf, lyapunov_rosenstein,
                estimate_lyapunov_from_curve, correlation_dimension,
                lyapunov_spectrum, poincare_section,
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
                self.progress.emit("Calculating full Lyapunov spectrum (Sano-Sawada/QR)...")
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

            elif self.analysis_type == 'poincare':
                self.progress.emit("Calculating Poincare section...")
                from analysis.embedding import embed_timeseries
                embedded = embed_timeseries(self.data, self.m, self.tau)
                crossings = poincare_section(
                    embedded,
                    plane=self.poincare_plane,
                    direction=self.poincare_direction,
                )
                results['crossings'] = crossings
                results['m'] = self.m
                results['plane'] = self.poincare_plane

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
        self._embedded = None          # cached embedding for live Poincare
        self._slider_min = 0.0
        self._slider_max = 1.0
        self._poincare_timer = QTimer()
        self._poincare_timer.setSingleShot(True)
        self._poincare_timer.setInterval(150)   # 150 ms debounce
        self._poincare_timer.timeout.connect(self._run_poincare_live)
        self.init_ui()

    def init_ui(self):
        # Ana scroll area olustur
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Scroll icinde widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        # Parameters
        params_group = QGroupBox(self.tm("chaos_params"))
        params_layout = QFormLayout()

        self.tau_label = QLabel("t = ?")
        self.tau_label.setStyleSheet("font-weight: bold; color: #268bd2;")
        params_layout.addRow("Time Delay (τ):", self.tau_label)

        self.m_label = QLabel("m = ?")
        self.m_label.setStyleSheet("font-weight: bold; color: #268bd2;")
        params_layout.addRow("Embedding Dimension (m):", self.m_label)

        # Manuel override (opsiyonel)
        self.manual_tau_spin = QSpinBox()
        self.manual_tau_spin.setRange(1, 100)
        self.manual_tau_spin.setValue(10)
        self.manual_tau_spin.setEnabled(False)
        self.manual_tau_spin.setButtonSymbols(QSpinBox.UpDownArrows)
        params_layout.addRow("Manuel τ:", self.manual_tau_spin)

        self.manual_m_spin = QSpinBox()
        self.manual_m_spin.setRange(2, 20)
        self.manual_m_spin.setValue(3)
        self.manual_m_spin.setEnabled(False)
        self.manual_m_spin.setButtonSymbols(QSpinBox.UpDownArrows)
        params_layout.addRow("Manuel m:", self.manual_m_spin)

        self.use_manual_check = QPushButton(self.tm("chaos_manual_params"))
        self.use_manual_check.setCheckable(True)
        self.use_manual_check.toggled.connect(self._toggle_manual)
        params_layout.addRow("", self.use_manual_check)

        self.algo_combo = QComboBox()
        self.algo_combo.addItem(self.tm("chaos_wolf"), "wolf")
        self.algo_combo.addItem(self.tm("chaos_rosenstein"), "rosenstein")
        params_layout.addRow("Algorithm:", self.algo_combo)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # Lyapunov exponent
        lyap_group = QGroupBox(self.tm('analysis_lyapunov'))
        lyap_layout = QVBoxLayout()

        self.calc_lyap_button = QPushButton(self.tm('btn_calculate') + ' ' + self.tm('analysis_lyapunov'))
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
        spec_group = QGroupBox(self.tm("chaos_spectrum_group"))
        spec_layout = QVBoxLayout()

        self.calc_spec_button = QPushButton(self.tm("chaos_calc_spectrum"))
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

        self.calc_corr_button = QPushButton(self.tm('btn_calculate') + ' ' + self.tm('analysis_correlation_dim'))
        self.calc_corr_button.clicked.connect(self.calculate_correlation_dim)
        self.calc_corr_button.setEnabled(False)
        corr_layout.addWidget(self.calc_corr_button)

        self.corr_result_label = QLabel("D₂ = ?")
        self.corr_result_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #859900;")
        corr_layout.addWidget(self.corr_result_label)

        corr_group.setLayout(corr_layout)
        layout.addWidget(corr_group)

        # Poincare Section
        poincare_group = QGroupBox(self.tm('chaos_poincare_group'))
        poincare_layout = QVBoxLayout()

        # Axis selector
        axis_row = QHBoxLayout()
        axis_row.addWidget(QLabel(self.tm('chaos_poincare_axis') + ":"))
        self.poincare_axis_spin = QSpinBox()
        self.poincare_axis_spin.setRange(0, 19)
        self.poincare_axis_spin.setValue(0)
        self.poincare_axis_spin.setButtonSymbols(QSpinBox.UpDownArrows)
        self.poincare_axis_spin.setMaximumWidth(70)
        self.poincare_axis_spin.valueChanged.connect(self._on_poincare_axis_changed)
        axis_row.addWidget(self.poincare_axis_spin)
        axis_row.addStretch()
        poincare_layout.addLayout(axis_row)

        # Slider + live value label
        slider_header = QHBoxLayout()
        slider_header.addWidget(QLabel(self.tm('chaos_poincare_value') + ":"))
        self.poincare_value_label = QLabel("0.0000")
        self.poincare_value_label.setStyleSheet("font-weight: bold; color: #2aa198; min-width: 70px;")
        slider_header.addStretch()
        slider_header.addWidget(self.poincare_value_label)
        poincare_layout.addLayout(slider_header)

        self.poincare_slider = QSlider(Qt.Horizontal)
        self.poincare_slider.setRange(0, 1000)
        self.poincare_slider.setValue(500)
        self.poincare_slider.setEnabled(False)
        self.poincare_slider.valueChanged.connect(self._on_poincare_slider_moved)
        poincare_layout.addWidget(self.poincare_slider)

        # Min / Max labels below slider
        range_row = QHBoxLayout()
        self.poincare_min_label = QLabel("--")
        self.poincare_min_label.setStyleSheet("color: #888; font-size: 8pt;")
        self.poincare_max_label = QLabel("--")
        self.poincare_max_label.setStyleSheet("color: #888; font-size: 8pt;")
        self.poincare_max_label.setAlignment(Qt.AlignRight)
        range_row.addWidget(self.poincare_min_label)
        range_row.addStretch()
        range_row.addWidget(self.poincare_max_label)
        poincare_layout.addLayout(range_row)

        # Direction + Calculate
        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel(self.tm('chaos_poincare_dir') + ":"))
        self.poincare_dir_combo = QComboBox()
        self.poincare_dir_combo.addItem(self.tm('chaos_poincare_dir_up'), 1)
        self.poincare_dir_combo.addItem(self.tm('chaos_poincare_dir_down'), -1)
        self.poincare_dir_combo.addItem(self.tm('chaos_poincare_dir_both'), 0)
        self.poincare_dir_combo.currentIndexChanged.connect(self._schedule_poincare_update)
        dir_row.addWidget(self.poincare_dir_combo)
        dir_row.addStretch()
        poincare_layout.addLayout(dir_row)

        self.calc_poincare_button = QPushButton(self.tm('chaos_calc_poincare'))
        self.calc_poincare_button.clicked.connect(self.calculate_poincare)
        self.calc_poincare_button.setEnabled(False)
        poincare_layout.addWidget(self.calc_poincare_button)

        self.poincare_result_label = QLabel("N = ?")
        self.poincare_result_label.setStyleSheet(
            "font-size: 14pt; font-weight: bold; color: #2aa198;"
        )
        poincare_layout.addWidget(self.poincare_result_label)

        poincare_group.setLayout(poincare_layout)
        layout.addWidget(poincare_group)

        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Scroll area'yi main layout'a ekle
        scroll.setWidget(content_widget)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def set_data(self, timeseries, tau, m):
        self.current_data = timeseries
        self.tau = tau
        self.m = m
        self.tau_label.setText(f"τ = {tau}")
        self.m_label.setText(f"m = {m}")

        # Manuel spinbox'lara da default degerleri set et
        self.manual_tau_spin.setValue(tau)
        self.manual_m_spin.setValue(m)

        self.calc_lyap_button.setEnabled(True)
        self.calc_corr_button.setEnabled(True)
        self.calc_spec_button.setEnabled(True)
        self.calc_poincare_button.setEnabled(True)
        # Poincare ekseni maksimumunu m-1 ile sinirla
        self.poincare_axis_spin.setMaximum(max(0, m - 1))

        # Cache the embedding so the live slider can use it without re-computing
        try:
            from analysis.embedding import embed_timeseries
            self._embedded = embed_timeseries(timeseries.data, m, tau)
        except Exception:
            self._embedded = None

        # Set initial slider range and enable it
        self._update_slider_range(self.poincare_axis_spin.value())

    def reset_data(self, timeseries=None):
        """Clear cached parameters and results when the source series changes."""
        self.current_data = timeseries
        self.tau = None
        self.m = None
        self._embedded = None
        self.tau_label.setText("τ = ?")
        self.m_label.setText("m = ?")
        self.lyap_result_label.setText("λ = ?")
        self.lyap_info.clear()
        self.spec_result_label.setText("λ₁, λ₂, ... = ?")
        self.spec_info.clear()
        self.corr_result_label.setText("D₂ = ?")
        self.poincare_result_label.setText("N = ?")
        self.poincare_min_label.setText("--")
        self.poincare_max_label.setText("--")
        self.poincare_value_label.setText("0.0000")
        self.poincare_slider.setEnabled(False)
        self.status_label.setText("")
        self.progress.setVisible(False)
        self.calc_lyap_button.setEnabled(False)
        self.calc_corr_button.setEnabled(False)
        self.calc_spec_button.setEnabled(False)
        self.calc_poincare_button.setEnabled(False)

    def calculate_lyapunov(self):
        if not self._check_ready():
            return
        tau, m = self._get_params()
        algo = self.algo_combo.currentData()
        self.worker = ChaosWorker(
            self.current_data.data, tau, m,
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
        tau, m = self._get_params()
        self.worker = ChaosWorker(
            self.current_data.data, tau, m,
            'spectrum', dt=self.current_data.dt
        )
        self.worker.finished.connect(self.on_spectrum_complete)
        self.worker.error.connect(self.on_error)
        self.worker.progress.connect(self.on_progress)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.calc_spec_button.setEnabled(False)
        self.worker.start()

    def calculate_poincare(self):
        if not self._check_ready():
            return
        tau, m = self._get_params()
        axis = self.poincare_axis_spin.value()
        axis = min(axis, m - 1)
        plane = {"axis": axis, "value": self._slider_to_value()}
        direction = self.poincare_dir_combo.currentData()
        self.worker = ChaosWorker(
            self.current_data.data, tau, m,
            'poincare', dt=self.current_data.dt,
            poincare_plane=plane, poincare_direction=direction,
        )
        self.worker.finished.connect(self.on_poincare_complete)
        self.worker.error.connect(self.on_error)
        self.worker.progress.connect(self.on_progress)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.calc_poincare_button.setEnabled(False)
        self.worker.start()

    def calculate_correlation_dim(self):
        if not self._check_ready():
            return
        tau, m = self._get_params()
        self.worker = ChaosWorker(self.current_data.data, tau, m, 'correlation_dim')
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

    def on_poincare_complete(self, results):
        self.progress.setVisible(False)
        self.calc_poincare_button.setEnabled(True)
        self.status_label.setText("")

        crossings = results.get('crossings', np.empty((0, 2)))
        n = len(crossings)
        self.poincare_result_label.setText(f"N = {n} crossing points")

        self.plot_requested.emit({
            'type': 'chaos_poincare',
            'crossings': crossings,
            'plane': results.get('plane', {}),
            'm': results.get('m', 2),
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
        self.calc_poincare_button.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")

    def _check_ready(self):
        return (self.current_data is not None and
                self.tau is not None and
                self.m is not None)

    def _toggle_manual(self, checked):
        """Manuel parametre girisini ac/kapat"""
        self.manual_tau_spin.setEnabled(checked)
        self.manual_m_spin.setEnabled(checked)

    def _get_params(self):
        """Aktif parametreleri al (otomatik veya manuel)"""
        if self.use_manual_check.isChecked():
            tau = self.manual_tau_spin.value()
            m = self.manual_m_spin.value()
        else:
            tau = self.tau
            m = self.m
        return tau, m

    # Poincare live-slider helpers

    def _update_slider_range(self, axis):
        """Recalculate min/max for the given embedding axis and update UI."""
        if self._embedded is None or axis >= self._embedded.shape[1]:
            self.poincare_min_label.setText("--")
            self.poincare_max_label.setText("--")
            self.poincare_slider.setEnabled(False)
            return

        col = self._embedded[:, axis]
        self._slider_min = float(col.min())
        self._slider_max = float(col.max())

        self.poincare_min_label.setText(f"{self._slider_min:.4g}")
        self.poincare_max_label.setText(f"{self._slider_max:.4g}")
        self.poincare_slider.setEnabled(True)

        # Set slider to mid-point and refresh label
        self.poincare_slider.blockSignals(True)
        self.poincare_slider.setValue(500)
        self.poincare_slider.blockSignals(False)
        mid = (self._slider_min + self._slider_max) / 2.0
        self.poincare_value_label.setText(f"{mid:.4g}")

    def _slider_to_value(self):
        """Map slider integer 0-1000 to float in [_slider_min, _slider_max]."""
        t = self.poincare_slider.value() / 1000.0
        return self._slider_min + t * (self._slider_max - self._slider_min)

    def _on_poincare_axis_changed(self, axis):
        """Called when the axis spinbox changes -- recalibrate slider range."""
        self._update_slider_range(axis)
        self._schedule_poincare_update()

    def _on_poincare_slider_moved(self, value):
        """Called on every slider tick -- update the displayed value and debounce."""
        val = self._slider_to_value()
        self.poincare_value_label.setText(f"{val:.4g}")
        self._schedule_poincare_update()

    def _schedule_poincare_update(self):
        """Restart the debounce timer if embedding data is ready."""
        if self._embedded is not None:
            self._poincare_timer.start()

    def _run_poincare_live(self):
        """Synchronous Poincare section on cached embedding -- fast, pure numpy."""
        if self._embedded is None:
            return
        try:
            from analysis import poincare_section
        except ImportError:
            return

        axis = self.poincare_axis_spin.value()
        axis = min(axis, self._embedded.shape[1] - 1)
        value = self._slider_to_value()
        direction = self.poincare_dir_combo.currentData()

        plane = {"axis": axis, "value": value}
        try:
            crossings = poincare_section(self._embedded, plane=plane, direction=direction)
        except Exception as e:
            self.status_label.setText(f"Poincare error: {e}")
            return

        n = len(crossings)
        self.poincare_result_label.setText(f"N = {n} crossing points")

        self.plot_requested.emit({
            'type': 'chaos_poincare',
            'crossings': crossings,
            'plane': plane,
            'm': self._embedded.shape[1],
        })

    def refresh_ui(self):
        self.calc_lyap_button.setText(self.tm('btn_calculate') + ' ' + self.tm('analysis_lyapunov'))
        self.calc_corr_button.setText(self.tm('btn_calculate') + ' ' + self.tm('analysis_correlation_dim'))
