"""
Grafik paneli — sag tarafta tum grafikleri gosterir.
ContentPanel'den gelen plot_requested sinyallerini isler.
Split layout: ust panel (aktif), alt panel (karsilastirma icin secilmis grafik).
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QSplitter, QGroupBox
)
from PySide6.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from typing import Dict, List, Optional


class PlotPanel(QWidget):
    """Sag panel: ust/alt split grafik + gecmis sistemi"""

    def __init__(self, theme_manager):
        super().__init__()
        self.theme_manager = theme_manager
        
        # Plot history (son 20 grafik sakla)
        self.plot_history: List[Dict] = []
        self.max_history = 20
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Vertical splitter: ust grafik + alt grafik
        self.vsplitter = QSplitter(Qt.Vertical)

        # --- UST GRAFIK (aktif grafik) ---
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        self.top_title_label = QLabel("Grafik")
        self.top_title_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        top_layout.addWidget(self.top_title_label)

        self.top_plot_widget = pg.PlotWidget()
        self.top_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.top_plot_widget.addLegend()
        self._apply_theme(self.top_plot_widget)
        top_layout.addWidget(self.top_plot_widget)

        self.vsplitter.addWidget(top_widget)

        # --- ALT GRAFIK (karsilastirma icin) ---
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # Kontrol satiri: dropdown + clear button
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("Karsilastirma Grafigi:"))
        
        self.bottom_combo = QComboBox()
        self.bottom_combo.addItem("(Bos)")
        self.bottom_combo.currentIndexChanged.connect(self._on_bottom_combo_changed)
        control_layout.addWidget(self.bottom_combo, 1)
        
        self.clear_bottom_btn = QPushButton("Temizle")
        self.clear_bottom_btn.clicked.connect(self._clear_bottom_plot)
        control_layout.addWidget(self.clear_bottom_btn)
        
        bottom_layout.addLayout(control_layout)

        self.bottom_title_label = QLabel("(Bos)")
        self.bottom_title_label.setStyleSheet("font-size: 10pt; font-style: italic;")
        bottom_layout.addWidget(self.bottom_title_label)

        self.bottom_plot_widget = pg.PlotWidget()
        self.bottom_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.bottom_plot_widget.addLegend()
        self._apply_theme(self.bottom_plot_widget)
        bottom_layout.addWidget(self.bottom_plot_widget)

        self.vsplitter.addWidget(bottom_widget)

        # Split oranlari: %60 ust, %40 alt
        self.vsplitter.setSizes([600, 400])

        layout.addWidget(self.vsplitter)

    def clear_plot(self):
        """Tüm grafikleri temizle"""
        self.top_plot_widget.clear()
        self.top_title_label.setText("Grafik")
        self.bottom_plot_widget.clear()
        self.bottom_title_label.setText("(Bos)")
        self.bottom_combo.setCurrentIndex(0)

    def handle_plot(self, plot_data: dict):
        """
        ContentPanel'den gelen plot isteklerini isler.
        Her grafik history'e eklenir ve ust panelde gosterilir.
        """
        ptype = plot_data.get('type', '')

        # Grafigi ciz (ust panel)
        if ptype == 'timeseries':
            self._plot_timeseries(plot_data, self.top_plot_widget, self.top_title_label)
        elif ptype == 'linear':
            self._plot_linear(plot_data, self.top_plot_widget, self.top_title_label)
        elif ptype == 'param_tau':
            self._plot_param_tau(plot_data, self.top_plot_widget, self.top_title_label)
        elif ptype == 'param_m':
            self._plot_param_m(plot_data, self.top_plot_widget, self.top_title_label)
        elif ptype == 'chaos_lyapunov':
            self._plot_chaos_lyapunov(plot_data, self.top_plot_widget, self.top_title_label)
        elif ptype == 'chaos_spectrum':
            self._plot_chaos_spectrum(plot_data, self.top_plot_widget, self.top_title_label)
        elif ptype == 'chaos_correlation':
            self._plot_chaos_correlation(plot_data, self.top_plot_widget, self.top_title_label)
        elif ptype == 'preprocessing':
            self._plot_preprocessing(plot_data, self.top_plot_widget, self.top_title_label)
        elif ptype == 'embedding_2d':
            self._plot_embedding_2d(plot_data, self.top_plot_widget, self.top_title_label)
        elif ptype == 'embedding_3d':
            self._plot_embedding_3d(plot_data, self.top_plot_widget, self.top_title_label)
        elif ptype == 'return_map':
            self._plot_return_map(plot_data, self.top_plot_widget, self.top_title_label)

        # Auto-range (grafigi tam ekrana sigdir)
        self.top_plot_widget.autoRange()

        # History'e ekle
        self._add_to_history(plot_data)

    def _add_to_history(self, plot_data: dict):
        """Grafik history'e ekle ve dropdown'u guncelle"""
        # Title olustur
        ptype = plot_data.get('type', 'Unknown')
        title = self._generate_title(plot_data)
        
        # History'e ekle
        entry = {
            'data': plot_data.copy(),
            'title': title,
            'timestamp': len(self.plot_history)  # Basit ID
        }
        self.plot_history.append(entry)
        
        # Max history limitini koru
        if len(self.plot_history) > self.max_history:
            self.plot_history.pop(0)
        
        # Dropdown'u guncelle
        self._update_bottom_combo()

    def _generate_title(self, plot_data: dict) -> str:
        """Plot data'dan okunabilir title olustur"""
        ptype = plot_data.get('type', 'Unknown')
        
        if ptype == 'timeseries':
            return "Time Series"
        elif ptype == 'linear':
            atype = plot_data.get('analysis_type', 'acf').upper()
            return f"Linear: {atype}"
        elif ptype == 'param_tau':
            return "AMI (τ estimation)"
        elif ptype == 'param_m':
            return "FNN (m estimation)"
        elif ptype == 'chaos_lyapunov':
            algo = plot_data.get('results', {}).get('algorithm', 'Unknown')
            return f"Lyapunov: {algo}"
        elif ptype == 'chaos_spectrum':
            return "Lyapunov Spectrum"
        elif ptype == 'chaos_correlation':
            return "Correlation Dimension"
        elif ptype == 'preprocessing':
            op = plot_data.get('operation', 'Unknown')
            return f"Preprocessing: {op}"
        elif ptype == 'embedding_2d':
            tau = plot_data.get('tau', '?')
            return f"2D Faz Uzayı (τ={tau})"
        elif ptype == 'embedding_3d':
            tau = plot_data.get('tau', '?')
            return f"3D Faz Uzayı (τ={tau})"
        elif ptype == 'return_map':
            return "Geri Dönüş Haritası"
        else:
            return f"Plot ({ptype})"

    def _update_bottom_combo(self):
        """Dropdown menu'yu history'den guncelle"""
        # Mevcut secimi sakla
        current_text = self.bottom_combo.currentText()
        
        # Combobox'i temizle
        self.bottom_combo.blockSignals(True)
        self.bottom_combo.clear()
        self.bottom_combo.addItem("(Bos)")
        
        # History'den ekle (ters sirada, en yeni ustte)
        for entry in reversed(self.plot_history):
            self.bottom_combo.addItem(entry['title'])
        
        self.bottom_combo.blockSignals(False)
        
        # Eski secimi geri yukle
        idx = self.bottom_combo.findText(current_text)
        if idx >= 0:
            self.bottom_combo.setCurrentIndex(idx)

    def _on_bottom_combo_changed(self, index: int):
        """Alt panel dropdown'da secim degistiginde"""
        if index == 0:  # "(Bos)"
            self._clear_bottom_plot()
            return
        
        # History'den secilen grafigi bul (index-1 cunku ilk item "(Bos)")
        history_idx = len(self.plot_history) - index  # Ters sirada
        if 0 <= history_idx < len(self.plot_history):
            entry = self.plot_history[history_idx]
            self._render_plot_to_widget(
                entry['data'], 
                self.bottom_plot_widget, 
                self.bottom_title_label
            )
            # Auto-range
            self.bottom_plot_widget.autoRange()

    def _clear_bottom_plot(self):
        """Alt paneli temizle"""
        self.bottom_plot_widget.clear()
        self.bottom_title_label.setText("(Bos)")
        self.bottom_combo.blockSignals(True)
        self.bottom_combo.setCurrentIndex(0)
        self.bottom_combo.blockSignals(False)

    def _render_plot_to_widget(self, plot_data: dict, widget: pg.PlotWidget, title_label: QLabel):
        """Belirli bir plot_data'yi widget'a ciz"""
        ptype = plot_data.get('type', '')

        if ptype == 'timeseries':
            self._plot_timeseries(plot_data, widget, title_label)
        elif ptype == 'linear':
            self._plot_linear(plot_data, widget, title_label)
        elif ptype == 'param_tau':
            self._plot_param_tau(plot_data, widget, title_label)
        elif ptype == 'param_m':
            self._plot_param_m(plot_data, widget, title_label)
        elif ptype == 'chaos_lyapunov':
            self._plot_chaos_lyapunov(plot_data, widget, title_label)
        elif ptype == 'chaos_spectrum':
            self._plot_chaos_spectrum(plot_data, widget, title_label)
        elif ptype == 'chaos_correlation':
            self._plot_chaos_correlation(plot_data, widget, title_label)
        elif ptype == 'preprocessing':
            self._plot_preprocessing(plot_data, widget, title_label)
        elif ptype == 'embedding_2d':
            self._plot_embedding_2d(plot_data, widget, title_label)
        elif ptype == 'embedding_3d':
            self._plot_embedding_3d(plot_data, widget, title_label)
        elif ptype == 'return_map':
            self._plot_return_map(plot_data, widget, title_label)

    # ------------------------------------------------------------------
    # PLOT FUNCTIONS (her biri artik widget + title_label alir)
    # ------------------------------------------------------------------
    
    def _plot_timeseries(self, d, widget, title_label):
        widget.clear()
        widget.setLogMode(y=False)
        widget.setLabel('left', 'Value')
        widget.setLabel('bottom', 'Time')
        title_label.setText("Time Series")
        widget.plot(d['time'], d['data'],
                    pen=pg.mkPen(color='#0e639c', width=1.5),
                    name='Time Series')

    def _plot_linear(self, d, widget, title_label):
        widget.clear()
        widget.setLogMode(y=False)
        atype = d.get('analysis_type', 'acf')
        results = d['results']
        n = d.get('n_data', 1000)

        if atype == 'acf':
            title_label.setText("ACF")
            widget.setLabel('left', 'ACF')
            widget.setLabel('bottom', 'Lag')
            widget.plot(results['lags'], results['acf'],
                        pen=pg.mkPen(color='#0e639c', width=2))
            conf = 1.96 / np.sqrt(n)
            widget.plot(results['lags'], [conf] * len(results['lags']),
                        pen=pg.mkPen(color='red', style=Qt.DashLine))
            widget.plot(results['lags'], [-conf] * len(results['lags']),
                        pen=pg.mkPen(color='red', style=Qt.DashLine))
        elif atype == 'pacf':
            title_label.setText("PACF")
            widget.setLabel('left', 'PACF')
            widget.setLabel('bottom', 'Lag')
            widget.plot(results['lags'], results['pacf'],
                        pen=pg.mkPen(color='#859900', width=2))
        elif atype == 'fft':
            title_label.setText("FFT Power Spectrum")
            widget.setLabel('left', 'Power')
            widget.setLabel('bottom', 'Frequency (Hz)')
            widget.plot(results['frequencies'], results['power'],
                        pen=pg.mkPen(color='#d33682', width=1.5))
            widget.setLogMode(y=True)

    def _plot_param_tau(self, d, widget, title_label):
        widget.clear()
        widget.setLogMode(y=False)
        title_label.setText("AMI — Time Delay Estimation")
        widget.setLabel('left', 'AMI')
        widget.setLabel('bottom', 'Lag')
        results = d['results']
        widget.plot(results['lags'], results['ami'],
                    pen=pg.mkPen(color='#268bd2', width=2))
        tau = results['tau']
        ami = results['ami']
        if 0 < tau <= len(ami):
            widget.plot([tau], [ami[tau - 1]],
                        pen=None, symbol='o', symbolSize=10,
                        symbolBrush='red')

    def _plot_param_m(self, d, widget, title_label):
        widget.clear()
        widget.setLogMode(y=False)
        title_label.setText("FNN — Embedding Dimension Estimation")
        widget.setLabel('left', 'FNN %')
        widget.setLabel('bottom', 'Dimension')
        results = d['results']
        widget.plot(results['dimensions'], results['fnn'],
                    pen=pg.mkPen(color='#859900', width=2))
        widget.plot(results['dimensions'],
                    [1.0] * len(results['dimensions']),
                    pen=pg.mkPen(color='red', style=Qt.DashLine))

    def _plot_chaos_lyapunov(self, d, widget, title_label):
        widget.clear()
        widget.setLogMode(y=False)
        results = d['results']
        algo = results.get('algorithm', '')
        title_label.setText(f"Lyapunov — {algo}")

        if 't_steps' in results and 'divergence' in results:
            widget.setLabel('left', 'ln(divergence)')
            widget.setLabel('bottom', 'Time')
            t = results['t_steps']
            div = results['divergence']
            valid = ~np.isnan(div)
            widget.plot(t[valid], div[valid],
                        pen=pg.mkPen(color='#0e639c', width=2))
        else:
            widget.setLabel('left', 'λ')
            widget.setLabel('bottom', '')
            lyap = results.get('lyapunov', 0)
            widget.plot([0], [lyap],
                        pen=None, symbol='o', symbolSize=15,
                        symbolBrush='#0e639c')

    def _plot_chaos_spectrum(self, d, widget, title_label):
        widget.clear()
        widget.setLogMode(y=False)
        title_label.setText("Lyapunov Spectrum")
        widget.setLabel('left', 'λ (nats/s)')
        widget.setLabel('bottom', 'Exponent Index')
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
        widget.addItem(bg)
        widget.addLine(y=0, pen=pg.mkPen('#888888', width=1,
                                          style=Qt.DashLine))

    def _plot_chaos_correlation(self, d, widget, title_label):
        widget.clear()
        widget.setLogMode(y=False)
        title_label.setText("Correlation Dimension")
        widget.setLabel('left', 'log(C(r))')
        widget.setLabel('bottom', 'log(r)')
        results = d['results']
        radii = results['radii']
        c_r = results['c_r']
        valid = c_r > 0
        if np.any(valid):
            log_r = np.log(radii[valid])
            log_c = np.log(c_r[valid])
            widget.plot(log_r, log_c,
                        pen=pg.mkPen(color='#859900', width=2),
                        symbol='o', symbolSize=5)

    def _plot_preprocessing(self, d, widget, title_label):
        widget.clear()
        widget.setLogMode(y=False)
        title_label.setText(f"Preprocessing — {d.get('operation', '')}")
        widget.setLabel('left', 'Value')
        widget.setLabel('bottom', 'Time')

        # Orijinal veri (soluk)
        if d.get('data_original') is not None:
            widget.plot(d['time_original'], d['data_original'],
                        pen=pg.mkPen(color='#555555', width=1),
                        name='Original')
        # Islenmis veri
        widget.plot(d['time_processed'], d['data_processed'],
                    pen=pg.mkPen(color='#0e639c', width=1.5),
                    name='Processed')

    def _plot_embedding_2d(self, d, widget, title_label):
        """2D Faz Uzayı: x(t) vs x(t+τ)"""
        widget.clear()
        widget.setLogMode(y=False)
        tau = d.get('tau', '?')
        title_label.setText(f"2D Faz Uzayı (τ={tau})")
        widget.setLabel('left', f'x(t+{tau})')
        widget.setLabel('bottom', 'x(t)')
        
        x = d['x']
        y = d['y']
        
        # Scatter plot (trajectory)
        widget.plot(x, y, pen=pg.mkPen(color='#0e639c', width=1.5))
        
        # İlk nokta (başlangıç) kırmızı
        widget.plot([x[0]], [y[0]], 
                    pen=None, symbol='o', symbolSize=8, 
                    symbolBrush='#dc322f', name='Start')
        
        # Son nokta (bitiş) yeşil
        widget.plot([x[-1]], [y[-1]], 
                    pen=None, symbol='s', symbolSize=8, 
                    symbolBrush='#859900', name='End')

    def _plot_embedding_3d(self, d, widget, title_label):
        """3D Faz Uzayı: x(t), x(t+τ), x(t+2τ)"""
        # PyQtGraph 2D plot widget'ında 3D gösteremeyiz
        # Bunun yerine 3 projection gösterelim veya mesaj verelim
        widget.clear()
        widget.setLogMode(y=False)
        tau = d.get('tau', '?')
        title_label.setText(f"3D Faz Uzayı (τ={tau}) - 2D İzdüşüm")
        
        x = d['x']
        y = d['y']
        z = d.get('z')
        
        if z is not None:
            # XY projection göster
            widget.setLabel('left', f'x(t+{tau})')
            widget.setLabel('bottom', 'x(t)')
            
            # Z değerini renge kodla (color-coded)
            z_norm = (z - z.min()) / (z.max() - z.min() + 1e-10)
            
            # Gradient: mavi -> kırmızı
            colors = []
            for zn in z_norm:
                # HSV color: hue 240 (blue) -> 0 (red)
                hue = int(240 * (1 - zn))
                colors.append(pg.mkBrush(f'hsv({hue}, 255, 200)'))
            
            # Scatter plot with color coding
            scatter = pg.ScatterPlotItem(
                x=x, y=y, 
                size=3, 
                brush=colors,
                pen=None
            )
            widget.addItem(scatter)
            
            # Başlangıç/bitiş noktaları
            widget.plot([x[0]], [y[0]], 
                        pen=None, symbol='o', symbolSize=10, 
                        symbolBrush='#dc322f', name='Start')
            widget.plot([x[-1]], [y[-1]], 
                        pen=None, symbol='s', symbolSize=10, 
                        symbolBrush='#859900', name='End')

    def _plot_return_map(self, d, widget, title_label):
        """Geri Dönüş Haritası: x(t) vs x(t+1)"""
        widget.clear()
        widget.setLogMode(y=False)
        title_label.setText("Geri Dönüş Haritası")
        widget.setLabel('left', 'x(t+1)')
        widget.setLabel('bottom', 'x(t)')
        
        x = d['x']
        y = d['y']
        
        # Scatter plot
        scatter = pg.ScatterPlotItem(
            x=x, y=y,
            size=2,
            pen=pg.mkPen(None),
            brush=pg.mkBrush('#268bd2')
        )
        widget.addItem(scatter)
        
        # Diagonal line (y=x)
        x_range = [x.min(), x.max()]
        widget.plot(x_range, x_range, 
                    pen=pg.mkPen('#dc322f', style=Qt.DashLine, width=1),
                    name='y=x')

    # ------------------------------------------------------------------
    def update_plot_theme(self):
        self._apply_theme(self.top_plot_widget)
        self._apply_theme(self.bottom_plot_widget)

    def _apply_theme(self, pw: pg.PlotWidget):
        theme = self.theme_manager.get_theme()
        pw.setBackground(theme.colors['plot_bg'])
        for axis in ['left', 'bottom', 'right', 'top']:
            ax = pw.getAxis(axis)
            ax.setPen(pg.mkPen(color=theme.colors['plot_text'], width=1))
            ax.setTextPen(pg.mkPen(color=theme.colors['plot_text']))
