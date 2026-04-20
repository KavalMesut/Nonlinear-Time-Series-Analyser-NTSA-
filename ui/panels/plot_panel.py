"""
Grafik paneli — sag tarafta tum grafikleri gosterir.
ContentPanel'den gelen plot_requested sinyallerini isler.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)
from PySide6.QtCore import Qt
import pyqtgraph as pg
import numpy as np


class PlotPanel(QWidget):
    """Sag panel: tum grafikleri barindirir"""

    def __init__(self, theme_manager):
        super().__init__()
        self.theme_manager = theme_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Baslik
        self.title_label = QLabel("Grafik")
        self.title_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        layout.addWidget(self.title_label)

        # Tek bir plot widget — tum analizler icin
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()
        self._apply_theme(self.plot_widget)
        layout.addWidget(self.plot_widget)

    def handle_plot(self, plot_data: dict):
        """ContentPanel'den gelen plot isteklerini isler"""
        ptype = plot_data.get('type', '')

        if ptype == 'timeseries':
            self._plot_timeseries(plot_data)
        elif ptype == 'linear':
            self._plot_linear(plot_data)
        elif ptype == 'param_tau':
            self._plot_param_tau(plot_data)
        elif ptype == 'param_m':
            self._plot_param_m(plot_data)
        elif ptype == 'chaos_lyapunov':
            self._plot_chaos_lyapunov(plot_data)
        elif ptype == 'chaos_spectrum':
            self._plot_chaos_spectrum(plot_data)
        elif ptype == 'chaos_correlation':
            self._plot_chaos_correlation(plot_data)
        elif ptype == 'preprocessing':
            self._plot_preprocessing(plot_data)

    # ------------------------------------------------------------------
    def _plot_timeseries(self, d):
        self.plot_widget.clear()
        self.plot_widget.setLogMode(y=False)
        self.plot_widget.setLabel('left', 'Value')
        self.plot_widget.setLabel('bottom', 'Time')
        self.title_label.setText("Time Series")
        self.plot_widget.plot(d['time'], d['data'],
                              pen=pg.mkPen(color='#0e639c', width=1.5),
                              name='Time Series')

    def _plot_linear(self, d):
        self.plot_widget.clear()
        self.plot_widget.setLogMode(y=False)
        atype = d.get('analysis_type', 'acf')
        results = d['results']
        n = d.get('n_data', 1000)

        if atype == 'acf':
            self.title_label.setText("ACF")
            self.plot_widget.setLabel('left', 'ACF')
            self.plot_widget.setLabel('bottom', 'Lag')
            self.plot_widget.plot(results['lags'], results['acf'],
                                  pen=pg.mkPen(color='#0e639c', width=2))
            conf = 1.96 / np.sqrt(n)
            self.plot_widget.plot(results['lags'], [conf] * len(results['lags']),
                                  pen=pg.mkPen(color='red', style=Qt.DashLine))
            self.plot_widget.plot(results['lags'], [-conf] * len(results['lags']),
                                  pen=pg.mkPen(color='red', style=Qt.DashLine))
        elif atype == 'pacf':
            self.title_label.setText("PACF")
            self.plot_widget.setLabel('left', 'PACF')
            self.plot_widget.setLabel('bottom', 'Lag')
            self.plot_widget.plot(results['lags'], results['pacf'],
                                  pen=pg.mkPen(color='#859900', width=2))
        elif atype == 'fft':
            self.title_label.setText("FFT Power Spectrum")
            self.plot_widget.setLabel('left', 'Power')
            self.plot_widget.setLabel('bottom', 'Frequency (Hz)')
            self.plot_widget.plot(results['frequencies'], results['power'],
                                  pen=pg.mkPen(color='#d33682', width=1.5))
            self.plot_widget.setLogMode(y=True)

    def _plot_param_tau(self, d):
        self.plot_widget.clear()
        self.plot_widget.setLogMode(y=False)
        self.title_label.setText("AMI — Time Delay Estimation")
        self.plot_widget.setLabel('left', 'AMI')
        self.plot_widget.setLabel('bottom', 'Lag')
        results = d['results']
        self.plot_widget.plot(results['lags'], results['ami'],
                              pen=pg.mkPen(color='#268bd2', width=2))
        tau = results['tau']
        ami = results['ami']
        if 0 < tau <= len(ami):
            self.plot_widget.plot([tau], [ami[tau - 1]],
                                  pen=None, symbol='o', symbolSize=10,
                                  symbolBrush='red')

    def _plot_param_m(self, d):
        self.plot_widget.clear()
        self.plot_widget.setLogMode(y=False)
        self.title_label.setText("FNN — Embedding Dimension Estimation")
        self.plot_widget.setLabel('left', 'FNN %')
        self.plot_widget.setLabel('bottom', 'Dimension')
        results = d['results']
        self.plot_widget.plot(results['dimensions'], results['fnn'],
                              pen=pg.mkPen(color='#859900', width=2))
        self.plot_widget.plot(results['dimensions'],
                              [1.0] * len(results['dimensions']),
                              pen=pg.mkPen(color='red', style=Qt.DashLine))

    def _plot_chaos_lyapunov(self, d):
        self.plot_widget.clear()
        self.plot_widget.setLogMode(y=False)
        results = d['results']
        algo = results.get('algorithm', '')
        self.title_label.setText(f"Lyapunov — {algo}")

        if 't_steps' in results and 'divergence' in results:
            self.plot_widget.setLabel('left', 'ln(divergence)')
            self.plot_widget.setLabel('bottom', 'Time')
            t = results['t_steps']
            div = results['divergence']
            valid = ~np.isnan(div)
            self.plot_widget.plot(t[valid], div[valid],
                                  pen=pg.mkPen(color='#0e639c', width=2))
        else:
            self.plot_widget.setLabel('left', 'λ')
            self.plot_widget.setLabel('bottom', '')
            lyap = results.get('lyapunov', 0)
            self.plot_widget.plot([0], [lyap],
                                  pen=None, symbol='o', symbolSize=15,
                                  symbolBrush='#0e639c')

    def _plot_chaos_spectrum(self, d):
        self.plot_widget.clear()
        self.plot_widget.setLogMode(y=False)
        self.title_label.setText("Lyapunov Spectrum")
        self.plot_widget.setLabel('left', 'λ (nats/s)')
        self.plot_widget.setLabel('bottom', 'Exponent Index')
        exponents = d['exponents']
        x = np.arange(len(exponents))
        colors = []
        for e in exponents:
            if e > 0.01:
                colors.append('#dc322f')
            elif e > -0.01:
                colors.append('#b58900')
            else:
                colors.append('#268bd2')
        bg = pg.BarGraphItem(x=x, height=exponents, width=0.6, brushes=colors)
        self.plot_widget.addItem(bg)
        self.plot_widget.addLine(y=0, pen=pg.mkPen('#888888', width=1,
                                                     style=Qt.DashLine))

    def _plot_chaos_correlation(self, d):
        self.plot_widget.clear()
        self.plot_widget.setLogMode(y=False)
        self.title_label.setText("Correlation Dimension")
        self.plot_widget.setLabel('left', 'log(C(r))')
        self.plot_widget.setLabel('bottom', 'log(r)')
        results = d['results']
        radii = results['radii']
        c_r = results['c_r']
        valid = c_r > 0
        if np.any(valid):
            log_r = np.log(radii[valid])
            log_c = np.log(c_r[valid])
            self.plot_widget.plot(log_r, log_c,
                                  pen=pg.mkPen(color='#859900', width=2),
                                  symbol='o', symbolSize=5)

    def _plot_preprocessing(self, d):
        self.plot_widget.clear()
        self.plot_widget.setLogMode(y=False)
        self.title_label.setText(f"Preprocessing — {d.get('operation', '')}")
        self.plot_widget.setLabel('left', 'Value')
        self.plot_widget.setLabel('bottom', 'Time')

        # Orijinal veri (soluk)
        if d.get('data_original') is not None:
            self.plot_widget.plot(d['time_original'], d['data_original'],
                                  pen=pg.mkPen(color='#555555', width=1),
                                  name='Original')
        # Islenmis veri
        self.plot_widget.plot(d['time_processed'], d['data_processed'],
                              pen=pg.mkPen(color='#0e639c', width=1.5),
                              name='Processed')

    # ------------------------------------------------------------------
    def update_plot_theme(self):
        self._apply_theme(self.plot_widget)

    def _apply_theme(self, pw: pg.PlotWidget):
        theme = self.theme_manager.get_theme()
        pw.setBackground(theme.colors['plot_bg'])
        for axis in ['left', 'bottom', 'right', 'top']:
            ax = pw.getAxis(axis)
            ax.setPen(pg.mkPen(color=theme.colors['plot_text'], width=1))
            ax.setTextPen(pg.mkPen(color=theme.colors['plot_text']))
