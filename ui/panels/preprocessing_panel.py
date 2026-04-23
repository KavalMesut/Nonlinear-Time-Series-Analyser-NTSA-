"""
On isleme (Preprocessing) paneli — kullanici islemleri secer, uygular, sonucu grafikte gosterir.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox,
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QFormLayout,
    QProgressBar, QStackedWidget
)
from PySide6.QtCore import Signal, QThread
import numpy as np
from core.timeseries import TimeSeries


class PreprocessWorker(QThread):
    """Arka planda on isleme calistirir"""
    finished = Signal(object, str)   # (islenmiş ndarray, islem adi)
    error = Signal(str)

    def __init__(self, data, operation, params):
        super().__init__()
        self.data = data
        self.operation = operation
        self.params = params

    def run(self):
        try:
            from core.preprocessing import (
                normalize, detrend, interpolate_missing, remove_outliers,
                smooth, difference, resample_data, filter_data,
                log_transform, boxcox_transform, window_crop, denoise
            )

            op = self.operation
            p = self.params

            if op == 'normalize':
                result = normalize(self.data, method=p.get('method', 'minmax'))
            elif op == 'detrend':
                result = detrend(self.data, method=p.get('method', 'linear'),
                                 poly_order=p.get('poly_order', 2))
            elif op == 'interpolate':
                result = interpolate_missing(self.data, method=p.get('method', 'linear'))
            elif op == 'outlier':
                result = remove_outliers(self.data, method=p.get('method', 'iqr'),
                                          threshold=p.get('threshold', 1.5))
            elif op == 'smooth':
                result = smooth(self.data, method=p.get('method', 'moving_avg'),
                                window_size=p.get('window_size', 5),
                                poly_order=p.get('poly_order', 3))
            elif op == 'difference':
                result = difference(self.data, order=p.get('order', 1))
            elif op == 'resample':
                result = resample_data(self.data, factor=p.get('factor', 1.0),
                                        method=p.get('method', 'interpolate'))
            elif op == 'filter':
                result = filter_data(self.data, filter_type=p.get('filter_type', 'lowpass'),
                                      cutoff=p.get('cutoff', 0.1),
                                      order=p.get('order', 4),
                                      fs=p.get('fs', 1.0),
                                      highcut=p.get('highcut', None))
            elif op == 'log_transform':
                result = log_transform(self.data)
            elif op == 'boxcox':
                result, _ = boxcox_transform(self.data)
            elif op == 'window':
                result = window_crop(self.data, start=p.get('start', 0),
                                      end=p.get('end', len(self.data)))
            elif op == 'denoise':
                result = denoise(self.data, method=p.get('method', 'wavelet'),
                                  level=p.get('level', 3))
            else:
                result = self.data.copy()

            self.finished.emit(result, op)
        except Exception as e:
            self.error.emit(str(e))


class PreprocessingPanel(QWidget):
    """On isleme paneli — kontroller"""

    plot_requested = Signal(dict)
    data_preprocessed = Signal(object)  # islenmis TimeSeries

    def __init__(self, translation_manager, theme_manager=None):
        super().__init__()
        self.tm = translation_manager
        self.theme_manager = theme_manager
        self.current_data = None      # orijinal TimeSeries
        self.processed_series = None  # son islenmis seri
        self.pending_input_series = None
        self.pending_params = None
        self.worker = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Islem secimi ---
        op_group = QGroupBox(self.tm('preprocess_operation'))
        op_layout = QFormLayout()

        self.op_combo = QComboBox()
        self._add_operations()
        self.op_combo.currentIndexChanged.connect(self._on_operation_changed)
        op_layout.addRow(QLabel(self.tm('preprocess_select')), self.op_combo)

        op_group.setLayout(op_layout)
        main_layout.addWidget(op_group)

        # --- Parametreler (stacked) ---
        self.params_group = QGroupBox(self.tm('preprocess_params'))
        params_outer = QVBoxLayout()
        self.params_stack = QStackedWidget()

        # 0: Normalize
        self.norm_page = QWidget()
        nl = QFormLayout(self.norm_page)
        self.norm_method = QComboBox()
        self.norm_method.addItem("Min-Max (0–1)", "minmax")
        self.norm_method.addItem("Z-Score", "zscore")
        nl.addRow(QLabel(self.tm('preprocess_method')), self.norm_method)
        self.params_stack.addWidget(self.norm_page)

        # 1: Detrend
        self.detrend_page = QWidget()
        dl = QFormLayout(self.detrend_page)
        self.detrend_method = QComboBox()
        self.detrend_method.addItem(self.tm('preprocess_linear'), "linear")
        self.detrend_method.addItem(self.tm('preprocess_polynomial'), "polynomial")
        self.detrend_method.addItem(self.tm('preprocess_mean_removal'), "mean")
        dl.addRow(QLabel(self.tm('preprocess_method')), self.detrend_method)
        self.detrend_poly = QSpinBox()
        self.detrend_poly.setRange(2, 10)
        self.detrend_poly.setValue(2)
        self.detrend_poly.setButtonSymbols(QSpinBox.UpDownArrows)
        dl.addRow(QLabel(self.tm('preprocess_poly_order')), self.detrend_poly)
        self.params_stack.addWidget(self.detrend_page)

        # 2: Interpolate missing
        self.interp_page = QWidget()
        il = QFormLayout(self.interp_page)
        self.interp_method = QComboBox()
        self.interp_method.addItem(self.tm('preprocess_linear'), "linear")
        self.interp_method.addItem("Spline (Cubic)", "spline")
        self.interp_method.addItem(self.tm('preprocess_nearest'), "nearest")
        il.addRow(QLabel(self.tm('preprocess_method')), self.interp_method)
        self.params_stack.addWidget(self.interp_page)

        # 3: Outlier removal
        self.outlier_page = QWidget()
        ol = QFormLayout(self.outlier_page)
        self.outlier_method = QComboBox()
        self.outlier_method.addItem("IQR", "iqr")
        self.outlier_method.addItem("Z-Score", "zscore")
        ol.addRow(QLabel(self.tm('preprocess_method')), self.outlier_method)
        self.outlier_threshold = QDoubleSpinBox()
        self.outlier_threshold.setRange(0.5, 10.0)
        self.outlier_threshold.setValue(1.5)
        self.outlier_threshold.setSingleStep(0.5)
        self.outlier_threshold.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
        ol.addRow(QLabel(self.tm('preprocess_threshold')), self.outlier_threshold)
        self.params_stack.addWidget(self.outlier_page)

        # 4: Smoothing
        self.smooth_page = QWidget()
        sl = QFormLayout(self.smooth_page)
        self.smooth_method = QComboBox()
        self.smooth_method.addItem(self.tm('preprocess_moving_avg'), "moving_avg")
        self.smooth_method.addItem("Savitzky-Golay", "savgol")
        sl.addRow(QLabel(self.tm('preprocess_method')), self.smooth_method)
        self.smooth_window = QSpinBox()
        self.smooth_window.setRange(3, 101)
        self.smooth_window.setValue(5)
        self.smooth_window.setSingleStep(2)
        self.smooth_window.setButtonSymbols(QSpinBox.UpDownArrows)
        sl.addRow(QLabel(self.tm('preprocess_window_size')), self.smooth_window)
        self.params_stack.addWidget(self.smooth_page)

        # 5: Differencing
        self.diff_page = QWidget()
        dfl = QFormLayout(self.diff_page)
        self.diff_order = QSpinBox()
        self.diff_order.setRange(1, 3)
        self.diff_order.setValue(1)
        self.diff_order.setButtonSymbols(QSpinBox.UpDownArrows)
        dfl.addRow(QLabel(self.tm('preprocess_diff_order')), self.diff_order)
        self.params_stack.addWidget(self.diff_page)

        # 6: Resampling
        self.resample_page = QWidget()
        rl = QFormLayout(self.resample_page)
        self.resample_factor = QDoubleSpinBox()
        self.resample_factor.setRange(0.1, 10.0)
        self.resample_factor.setValue(1.0)
        self.resample_factor.setSingleStep(0.1)
        self.resample_factor.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
        rl.addRow(QLabel(self.tm('preprocess_resample_factor')), self.resample_factor)
        self.params_stack.addWidget(self.resample_page)

        # 7: Filter
        self.filter_page = QWidget()
        fl = QFormLayout(self.filter_page)
        self.filter_type = QComboBox()
        self.filter_type.addItem(self.tm('preprocess_lowpass'), "lowpass")
        self.filter_type.addItem(self.tm('preprocess_highpass'), "highpass")
        self.filter_type.addItem(self.tm('preprocess_bandpass'), "bandpass")
        fl.addRow(QLabel(self.tm('preprocess_filter_type')), self.filter_type)
        self.filter_cutoff = QDoubleSpinBox()
        self.filter_cutoff.setRange(0.001, 100.0)
        self.filter_cutoff.setValue(0.1)
        self.filter_cutoff.setDecimals(3)
        self.filter_cutoff.setSingleStep(0.01)
        self.filter_cutoff.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
        fl.addRow(QLabel(self.tm('preprocess_cutoff')), self.filter_cutoff)
        self.filter_highcut = QDoubleSpinBox()
        self.filter_highcut.setRange(0.001, 100.0)
        self.filter_highcut.setValue(0.2)
        self.filter_highcut.setDecimals(3)
        self.filter_highcut.setSingleStep(0.01)
        self.filter_highcut.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
        self.filter_highcut_label = QLabel(self.tm('preprocess_highcut'))
        fl.addRow(self.filter_highcut_label, self.filter_highcut)
        self.filter_order = QSpinBox()
        self.filter_order.setRange(1, 10)
        self.filter_order.setValue(4)
        self.filter_order.setButtonSymbols(QSpinBox.UpDownArrows)
        fl.addRow(QLabel(self.tm('preprocess_filter_order')), self.filter_order)
        self.filter_type.currentIndexChanged.connect(self._on_filter_type_changed)
        self._on_filter_type_changed()
        self.params_stack.addWidget(self.filter_page)

        # 8: Log transform (parametre yok)
        self.log_page = QWidget()
        log_l = QVBoxLayout(self.log_page)
        log_l.addWidget(QLabel(self.tm('preprocess_log_info')))
        self.params_stack.addWidget(self.log_page)

        # 9: Box-Cox (parametre yok)
        self.boxcox_page = QWidget()
        bc_l = QVBoxLayout(self.boxcox_page)
        bc_l.addWidget(QLabel(self.tm('preprocess_boxcox_info')))
        self.params_stack.addWidget(self.boxcox_page)

        # 10: Windowing
        self.window_page = QWidget()
        wl = QFormLayout(self.window_page)
        self.window_start = QSpinBox()
        self.window_start.setRange(0, 999999)
        self.window_start.setValue(0)
        self.window_start.setButtonSymbols(QSpinBox.UpDownArrows)
        wl.addRow(QLabel(self.tm('preprocess_start_idx')), self.window_start)
        self.window_end = QSpinBox()
        self.window_end.setRange(1, 999999)
        self.window_end.setValue(1000)
        self.window_end.setButtonSymbols(QSpinBox.UpDownArrows)
        wl.addRow(QLabel(self.tm('preprocess_end_idx')), self.window_end)
        self.params_stack.addWidget(self.window_page)

        # 11: Denoise
        self.denoise_page = QWidget()
        dnl = QFormLayout(self.denoise_page)
        self.denoise_method = QComboBox()
        self.denoise_method.addItem(self.tm('preprocess_wavelet'), "wavelet")
        self.denoise_method.addItem(self.tm('preprocess_median_filter'), "median")
        dnl.addRow(QLabel(self.tm('preprocess_method')), self.denoise_method)
        self.denoise_level = QSpinBox()
        self.denoise_level.setRange(1, 10)
        self.denoise_level.setValue(3)
        self.denoise_level.setButtonSymbols(QSpinBox.UpDownArrows)
        dnl.addRow(QLabel(self.tm('preprocess_decomp_level')), self.denoise_level)
        self.params_stack.addWidget(self.denoise_page)

        params_outer.addWidget(self.params_stack)
        self.params_group.setLayout(params_outer)
        main_layout.addWidget(self.params_group)

        # --- Butonlar ---
        btn_layout = QHBoxLayout()

        self.apply_button = QPushButton(self.tm('btn_apply'))
        self.apply_button.setMinimumHeight(36)
        self.apply_button.clicked.connect(self._apply)
        self.apply_button.setEnabled(False)
        btn_layout.addWidget(self.apply_button)

        self.reset_button = QPushButton(self.tm('btn_reset'))
        self.reset_button.setMinimumHeight(36)
        self.reset_button.clicked.connect(self._reset)
        self.reset_button.setEnabled(False)
        btn_layout.addWidget(self.reset_button)

        main_layout.addLayout(btn_layout)

        # Ilerleme cubugu
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        main_layout.addWidget(self.progress)

        # Sonuc etiketi
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        main_layout.addWidget(self.result_label)

        main_layout.addStretch()

    # ----- islem listesini doldur -----
    def _add_operations(self):
        ops = [
            ('normalize', 'preprocess_normalize'),
            ('detrend', 'preprocess_detrend'),
            ('interpolate', 'preprocess_interpolate'),
            ('outlier', 'preprocess_outlier'),
            ('smooth', 'preprocess_smooth'),
            ('difference', 'preprocess_difference'),
            ('resample', 'preprocess_resample'),
            ('filter', 'preprocess_filter'),
            ('log_transform', 'preprocess_log'),
            ('boxcox', 'preprocess_boxcox'),
            ('window', 'preprocess_window'),
            ('denoise', 'preprocess_denoise'),
        ]
        for data_key, text_key in ops:
            self.op_combo.addItem(self.tm(text_key), data_key)

    # ----- slot'lar -----
    def _on_operation_changed(self):
        idx = self.op_combo.currentIndex()
        self.params_stack.setCurrentIndex(idx)

    def _on_filter_type_changed(self):
        is_band = (self.filter_type.currentData() == 'bandpass')
        self.filter_highcut.setVisible(is_band)
        self.filter_highcut_label.setVisible(is_band)

    def set_data(self, timeseries):
        """Veri yuklendikten sonra cagirilir"""
        self.current_data = timeseries
        self.processed_series = None
        self.pending_input_series = None
        self.pending_params = None
        self.apply_button.setEnabled(True)
        self.reset_button.setEnabled(False)
        self.result_label.setText("")

        # Windowing sinirlari guncelle
        self.window_end.setValue(len(timeseries))
        self.window_start.setMaximum(len(timeseries) - 1)
        self.window_end.setMaximum(len(timeseries))

    def _get_active_series(self):
        """Isleme alinacak seriyi dondurur."""
        if self.processed_series is not None:
            return self.processed_series
        if self.current_data is not None:
            return self.current_data
        return None

    def _apply(self):
        active_series = self._get_active_series()
        if active_series is None:
            return

        op = self.op_combo.currentData()
        params = self._collect_params(op)
        self.pending_input_series = active_series
        self.pending_params = params.copy()

        self.worker = PreprocessWorker(active_series.data.copy(), op, params)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)

        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.apply_button.setEnabled(False)
        self.worker.start()

    def _collect_params(self, op: str) -> dict:
        p = {}
        if op == 'normalize':
            p['method'] = self.norm_method.currentData()
        elif op == 'detrend':
            p['method'] = self.detrend_method.currentData()
            p['poly_order'] = self.detrend_poly.value()
        elif op == 'interpolate':
            p['method'] = self.interp_method.currentData()
        elif op == 'outlier':
            p['method'] = self.outlier_method.currentData()
            p['threshold'] = self.outlier_threshold.value()
        elif op == 'smooth':
            p['method'] = self.smooth_method.currentData()
            p['window_size'] = self.smooth_window.value()
        elif op == 'difference':
            p['order'] = self.diff_order.value()
        elif op == 'resample':
            p['factor'] = self.resample_factor.value()
        elif op == 'filter':
            p['filter_type'] = self.filter_type.currentData()
            p['cutoff'] = self.filter_cutoff.value()
            p['highcut'] = self.filter_highcut.value()
            p['order'] = self.filter_order.value()
            if self.current_data:
                p['fs'] = 1.0 / self.current_data.dt
        elif op == 'window':
            p['start'] = self.window_start.value()
            p['end'] = self.window_end.value()
        elif op == 'denoise':
            p['method'] = self.denoise_method.currentData()
            p['level'] = self.denoise_level.value()
        return p

    def _build_result_series(self, input_series: TimeSeries, result: np.ndarray,
                             op_name: str, params: dict) -> TimeSeries:
        dt = input_series.dt
        t0 = input_series.t0

        if op_name == 'difference':
            shift = min(params.get('order', 1), max(0, len(input_series.data) - 1))
            t0 = input_series.t0 + shift * input_series.dt
        elif op_name == 'window':
            start = max(0, params.get('start', 0))
            t0 = input_series.t0 + start * input_series.dt
        elif op_name == 'resample' and len(result) > 1 and len(input_series.data) > 1:
            duration = input_series.time[-1] - input_series.time[0]
            dt = duration / (len(result) - 1)

        metadata = {
            **input_series.metadata,
            'preprocessed': True,
            'operation': op_name
        }
        return TimeSeries(data=result, dt=dt, metadata=metadata, t0=t0)

    def _on_finished(self, result: np.ndarray, op_name: str):
        self.progress.setVisible(False)
        self.apply_button.setEnabled(True)
        self.reset_button.setEnabled(True)
        input_series = self.pending_input_series or self._get_active_series()
        params = self.pending_params or {}
        processed_series = self._build_result_series(input_series, result, op_name, params)
        self.processed_series = processed_series
        self.pending_input_series = None
        self.pending_params = None

        # Sonuc ozeti
        op_label = self.op_combo.currentText()
        info = f"{op_label}: {len(result)} {self.tm('preprocess_points')}"
        self.result_label.setText(info)

        # Grafigi guncelle — orijinal + islenmis ustu uste
        time_orig = self.current_data.time if self.current_data else np.arange(len(result))
        time_proc = processed_series.time

        self.plot_requested.emit({
            'type': 'preprocessing',
            'time_original': time_orig,
            'data_original': self.current_data.data if self.current_data else None,
            'time_processed': time_proc,
            'data_processed': result,
            'operation': op_name
        })

        # islenmis veriyi TimeSeries olarak yayinla
        self.data_preprocessed.emit(processed_series)

    def _on_error(self, error_msg: str):
        self.progress.setVisible(False)
        self.apply_button.setEnabled(True)
        self.pending_input_series = None
        self.pending_params = None
        self.result_label.setText(f"{self.tm('msg_error')}: {error_msg}")

    def _reset(self):
        """Orijinal veriye geri don"""
        self.processed_series = None
        self.pending_input_series = None
        self.pending_params = None
        self.reset_button.setEnabled(False)
        self.result_label.setText(self.tm('preprocess_reset_done'))

        if self.current_data:
            self.plot_requested.emit({
                'type': 'timeseries',
                'time': self.current_data.time,
                'data': self.current_data.data,
                'metadata': self.current_data.metadata
            })
            self.data_preprocessed.emit(self.current_data)

    def refresh_ui(self):
        """Dil degistiginde UI'yi guncelle"""
        self.apply_button.setText(self.tm('btn_apply'))
        self.reset_button.setText(self.tm('btn_reset'))
        self.params_group.setTitle(self.tm('preprocess_params'))
        # Islem combo'sunu yeniden doldur
        current_idx = self.op_combo.currentIndex()
        self.op_combo.clear()
        self._add_operations()
        self.op_combo.setCurrentIndex(current_idx)
