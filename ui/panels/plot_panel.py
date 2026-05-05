"""
Grafik paneli — sag tarafta tum grafikleri gosterir.
ContentPanel'den gelen plot_requested sinyallerini isler.
Split layout: ust panel (aktif), alt panel (karsilastirma icin secilmis grafik).
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QSplitter, QGroupBox, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import numpy as np
from typing import Dict, List, Optional


class CustomGLViewWidget(gl.GLViewWidget):
    """
    Custom GLViewWidget with swapped mouse controls:
    - Right click + drag = Rotate (default: left click)
    - Left click + drag = Pan (default: middle click)
    """
    
    def mousePressEvent(self, ev: QMouseEvent):
        """Override mouse press to swap left/right button behavior"""
        # Swap left <-> right button
        if ev.button() == Qt.LeftButton:
            # Pretend it's middle button (pan)
            ev = QMouseEvent(
                ev.type(),
                ev.pos(),
                Qt.MiddleButton,  # Change to middle button
                Qt.MiddleButton,
                ev.modifiers()
            )
        elif ev.button() == Qt.RightButton:
            # Pretend it's left button (rotate)
            ev = QMouseEvent(
                ev.type(),
                ev.pos(),
                Qt.LeftButton,  # Change to left button
                Qt.LeftButton,
                ev.modifiers()
            )
        
        super().mousePressEvent(ev)
    
    def mouseMoveEvent(self, ev: QMouseEvent):
        """Override mouse move to swap left/right button behavior"""
        buttons = ev.buttons()
        
        # Swap left <-> right button states
        new_buttons = Qt.NoButton
        if buttons & Qt.LeftButton:
            new_buttons |= Qt.MiddleButton  # Pan
        if buttons & Qt.RightButton:
            new_buttons |= Qt.LeftButton  # Rotate
        if buttons & Qt.MiddleButton:
            new_buttons |= Qt.RightButton  # (original middle -> right)
        
        ev = QMouseEvent(
            ev.type(),
            ev.pos(),
            new_buttons,
            new_buttons,
            ev.modifiers()
        )
        
        super().mouseMoveEvent(ev)
    
    def mouseReleaseEvent(self, ev: QMouseEvent):
        """Override mouse release to swap left/right button behavior"""
        # Swap left <-> right button
        if ev.button() == Qt.LeftButton:
            ev = QMouseEvent(
                ev.type(),
                ev.pos(),
                Qt.MiddleButton,
                Qt.NoButton,
                ev.modifiers()
            )
        elif ev.button() == Qt.RightButton:
            ev = QMouseEvent(
                ev.type(),
                ev.pos(),
                Qt.LeftButton,
                Qt.NoButton,
                ev.modifiers()
            )
        
        super().mouseReleaseEvent(ev)


class PlotPanel(QWidget):
    """Sag panel: ust/alt split grafik + gecmis sistemi"""

    def __init__(self, theme_manager, plot_settings, translation_manager=None):
        super().__init__()
        self.theme_manager = theme_manager
        self.plot_settings = plot_settings
        self.tm = translation_manager if translation_manager is not None else (lambda key: key)
        
        # Plot history (son 20 grafik sakla)
        self.plot_history: List[Dict] = []
        self.max_history = 20

        # Adım bazlı sekme sistemi
        self._step_plots: Dict[int, List[Dict]] = {}   # {adım: [plot_data, ...]}
        self._active_tab_per_step: Dict[int, int] = {} # {adım: aktif_sekme_idx}
        self._current_tab_step: int = -1
        self.top_tab_buttons: List = []

        self.init_ui()
        self.refresh_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Vertical splitter: ust grafik + alt grafik
        self.vsplitter = QSplitter(Qt.Vertical)

        # --- UST GRAFIK (aktif grafik) ---
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        self.top_title_label = QLabel(self.tr("plot_title"))
        self.top_title_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        top_layout.addWidget(self.top_title_label)

        # Sekme satırı (birden fazla grafik olduğunda gösterilir)
        self.top_tab_row = QWidget()
        self.top_tab_layout = QHBoxLayout(self.top_tab_row)
        self.top_tab_layout.setContentsMargins(0, 2, 0, 2)
        self.top_tab_layout.setSpacing(4)
        self.top_tab_row.setVisible(False)
        top_layout.addWidget(self.top_tab_row)

        # Stack: 2D (PlotWidget) + 3D (GLViewWidget with overlay)
        self.top_stack = QStackedWidget()
        
        self.top_plot_widget = pg.PlotWidget()
        grid_alpha = self.plot_settings.get_grid_alpha_normalized()
        self.top_plot_widget.showGrid(x=True, y=True, alpha=grid_alpha)
        self.top_plot_widget.addLegend()
        self._apply_theme(self.top_plot_widget)
        self.top_stack.addWidget(self.top_plot_widget)  # index 0
        
        # 3D container (GLViewWidget + color bar overlay)
        top_3d_container = QWidget()
        top_3d_container.setLayout(QVBoxLayout())
        top_3d_container.layout().setContentsMargins(0, 0, 0, 0)
        
        self.top_3d_widget = CustomGLViewWidget()
        self._apply_theme_3d(self.top_3d_widget)
        top_3d_container.layout().addWidget(self.top_3d_widget)
        
        # Color bar overlay (sag alt kose)
        self.top_colorbar_label = self._create_colorbar_label()
        self.top_colorbar_label.setParent(top_3d_container)
        self.top_colorbar_label.hide()  # Baslangicta gizli
        
        self.top_stack.addWidget(top_3d_container)  # index 1
        
        top_layout.addWidget(self.top_stack)
        self.vsplitter.addWidget(top_widget)

        # --- ALT GRAFIK (karsilastirma icin) ---
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # Kontrol satiri: dropdown + clear button
        control_layout = QHBoxLayout()
        
        self.bottom_compare_label = QLabel(self.tr("plot_compare_label"))
        control_layout.addWidget(self.bottom_compare_label)
        
        self.bottom_combo = QComboBox()
        self.bottom_combo.addItem(self.tr("plot_empty"))
        self.bottom_combo.currentIndexChanged.connect(self._on_bottom_combo_changed)
        control_layout.addWidget(self.bottom_combo, 1)
        
        self.clear_bottom_btn = QPushButton(self.tr("plot_clear"))
        self.clear_bottom_btn.clicked.connect(self._clear_bottom_plot)
        control_layout.addWidget(self.clear_bottom_btn)
        
        bottom_layout.addLayout(control_layout)

        self.bottom_title_label = QLabel(self.tr("plot_empty"))
        self.bottom_title_label.setStyleSheet("font-size: 10pt; font-style: italic;")
        bottom_layout.addWidget(self.bottom_title_label)

        # Stack: 2D (PlotWidget) + 3D (GLViewWidget with overlay)
        self.bottom_stack = QStackedWidget()
        
        self.bottom_plot_widget = pg.PlotWidget()
        grid_alpha = self.plot_settings.get_grid_alpha_normalized()
        self.bottom_plot_widget.showGrid(x=True, y=True, alpha=grid_alpha)
        self.bottom_plot_widget.addLegend()
        self._apply_theme(self.bottom_plot_widget)
        self.bottom_stack.addWidget(self.bottom_plot_widget)  # index 0
        
        # 3D container (GLViewWidget + color bar overlay)
        bottom_3d_container = QWidget()
        bottom_3d_container.setLayout(QVBoxLayout())
        bottom_3d_container.layout().setContentsMargins(0, 0, 0, 0)
        
        self.bottom_3d_widget = CustomGLViewWidget()
        self._apply_theme_3d(self.bottom_3d_widget)
        bottom_3d_container.layout().addWidget(self.bottom_3d_widget)
        
        # Color bar overlay (sag alt kose)
        self.bottom_colorbar_label = self._create_colorbar_label()
        self.bottom_colorbar_label.setParent(bottom_3d_container)
        self.bottom_colorbar_label.hide()  # Baslangicta gizli
        
        self.bottom_stack.addWidget(bottom_3d_container)  # index 1
        
        bottom_layout.addWidget(self.bottom_stack)
        self.vsplitter.addWidget(bottom_widget)

        # Split oranlari: %50 ust, %50 alt
        self.vsplitter.setSizes([500, 500])
        
        # Splitter handle stilini ayarla (gorunur yap)
        self.vsplitter.setHandleWidth(6)
        self.vsplitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #555555;
                border: 1px solid #333333;
            }
            QSplitter::handle:hover {
                background-color: #777777;
            }
        """)

        layout.addWidget(self.vsplitter)

    def tr(self, key: str) -> str:
        return self.tm(key)
    
    def _get_pen(self, color=None, width=None):
        """Get pen with current settings"""
        if color is None:
            color = self.plot_settings.get('line_color')
        if width is None:
            width = self.plot_settings.get('line_width')
        return pg.mkPen(color=color, width=width)
    
    def apply_settings(self):
        """Apply current plot settings to all plots"""
        # Update grid alpha
        grid_alpha = self.plot_settings.get_grid_alpha_normalized()
        self.top_plot_widget.showGrid(x=True, y=True, alpha=grid_alpha)
        self.bottom_plot_widget.showGrid(x=True, y=True, alpha=grid_alpha)
        
        # Update font size and axis colors for both widgets
        self._apply_widget_settings(self.top_plot_widget)
        self._apply_widget_settings(self.bottom_plot_widget)
        
        # Update line width and scatter size for existing plot items
        self._update_plot_items(self.top_plot_widget)
        self._update_plot_items(self.bottom_plot_widget)
    
    def _update_plot_items(self, widget):
        """Update pen and symbol size for existing plot items"""
        new_pen = self._get_pen()
        scatter_size = self.plot_settings.get('scatter_size')
        
        # Update all PlotDataItem objects in the widget
        items = widget.items()
        
        for item in items:
            # Only process PlotDataItem (has opts attribute)
            if not hasattr(item, 'opts'):
                continue
            
            if hasattr(item, 'setPen'):
                # Check if it's a line plot (has pen)
                current_pen = item.opts.get('pen')
                if current_pen is not None and current_pen is not False:
                    item.setPen(new_pen)
            
            if hasattr(item, 'setSymbolSize'):
                # Check if it's a scatter plot (has symbols)
                if item.opts.get('symbol') is not None:
                    item.setSymbolSize(scatter_size)
    
    def _apply_widget_settings(self, widget):
        """Apply font and axis color settings to a plot widget"""
        font_size = self.plot_settings.get('font_size')
        axis_color = self.plot_settings.get('axis_color')
        
        # Update axis label styles
        for axis_name in ['left', 'bottom', 'right', 'top']:
            axis = widget.getAxis(axis_name)
            if axis:
                axis.setStyle(tickTextOffset=10)
                axis.setPen(axis_color)
                axis.setTextPen(axis_color)
                # Update font
                font = axis.font()
                font.setPointSize(font_size)
                axis.setTickFont(font)
    
    def _redraw_plot(self, plot_data: dict, target: str):
        """Redraw a plot with current settings"""
        ptype = plot_data.get('type', '')
        
        if target == 'top':
            widget = self.top_plot_widget
            title_label = self.top_title_label
            widget_3d = self.top_3d_widget
            stack = self.top_stack
        else:
            widget = self.bottom_plot_widget
            title_label = self.bottom_title_label
            widget_3d = self.bottom_3d_widget
            stack = self.bottom_stack
        
        # 3D grafik mi?
        if ptype == 'embedding_3d':
            stack.setCurrentIndex(1)
            self._plot_embedding_3d(plot_data, widget_3d, title_label)
        else:
            stack.setCurrentIndex(0)
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
            elif ptype == 'chaos_poincare':
                self._plot_poincare(plot_data, widget, title_label)
            elif ptype == 'chaos_bifurcation':
                self._plot_chaos_bifurcation(plot_data, widget, title_label)
            elif ptype == 'chaos_lyapunov_sweep':
                self._plot_chaos_lyapunov_sweep(plot_data, widget, title_label)

    def clear_plot(self):
        """Tüm grafikleri temizle"""
        # Adım sekme sistemini sıfırla
        self._step_plots.clear()
        self._active_tab_per_step.clear()
        self._current_tab_step = -1
        self.top_tab_buttons = []
        self.top_tab_row.setVisible(False)
        while self.top_tab_layout.count():
            item = self.top_tab_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        # 2D widget'lara gec ve temizle
        self.top_stack.setCurrentIndex(0)
        self.bottom_stack.setCurrentIndex(0)
        
        # Color bar'ları gizle
        self.top_colorbar_label.hide()
        self.bottom_colorbar_label.hide()
        
        self.top_plot_widget.clear()
        self.top_title_label.setText(self.tr("plot_title"))
        self.bottom_plot_widget.clear()
        self.bottom_title_label.setText(self.tr("plot_empty"))
        self.bottom_combo.setCurrentIndex(0)

    def handle_plot(self, plot_data: dict):
        """
        ContentPanel'den gelen plot isteklerini isler.
        Her grafik history'e eklenir ve ust panelde gosterilir.
        """
        ptype = plot_data.get('type', '')

        # 3D grafik mi kontrol et
        if ptype == 'embedding_3d':
            # 3D widget'a gec
            self.top_stack.setCurrentIndex(1)
            self._plot_embedding_3d(plot_data, self.top_3d_widget, self.top_title_label)
        else:
            # 2D widget'a gec
            self.top_stack.setCurrentIndex(0)
            # Color bar'ı gizle (2D grafiklerde görünmemeli)
            self.top_colorbar_label.hide()
            
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
            elif ptype == 'chaos_poincare':
                self._plot_poincare(plot_data, self.top_plot_widget, self.top_title_label)
            elif ptype == 'chaos_bifurcation':
                self._plot_chaos_bifurcation(plot_data, self.top_plot_widget, self.top_title_label)
            elif ptype == 'chaos_lyapunov_sweep':
                self._plot_chaos_lyapunov_sweep(plot_data, self.top_plot_widget, self.top_title_label)
            elif ptype == 'preprocessing':
                self._plot_preprocessing(plot_data, self.top_plot_widget, self.top_title_label)
            elif ptype == 'embedding_2d':
                self._plot_embedding_2d(plot_data, self.top_plot_widget, self.top_title_label)
            elif ptype == 'return_map':
                self._plot_return_map(plot_data, self.top_plot_widget, self.top_title_label)

            # Auto-range (grafigi tam ekrana sigdir)
            self.top_plot_widget.autoRange()

        # Adım sekme sistemini güncelle
        step = plot_data.get('_step')
        if step is not None:
            self._current_tab_step = step
            self._update_step_tabs(step, plot_data)

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
            return self.tr("plot_time_series")
        elif ptype == 'linear':
            atype = plot_data.get('analysis_type', 'acf').upper()
            return f"{self.tr('plot_linear')}: {atype}"
        elif ptype == 'param_tau':
            return "AMI (τ estimation)"
        elif ptype == 'param_m':
            return "FNN (m estimation)"
        elif ptype == 'chaos_lyapunov':
            algo = plot_data.get('results', {}).get('algorithm', 'Unknown')
            return f"Lyapunov: {algo}"
        elif ptype == 'chaos_spectrum':
            return self.tr("plot_lyapunov_spectrum")
        elif ptype == 'chaos_correlation':
            return self.tr("plot_correlation_dim")
        elif ptype == 'chaos_bifurcation':
            sys_name = plot_data.get('system', '?')
            sweep_p = plot_data.get('sweep_param', '?')
            return f"Bifurcation: {sys_name} ({sweep_p})"
        elif ptype == 'chaos_lyapunov_sweep':
            sys_name = plot_data.get('system', '?')
            sweep_p = plot_data.get('sweep_param', '?')
            method = plot_data.get('method', '?')
            return f"Lyapunov sweep: {sys_name} ({sweep_p}, {method})"
        elif ptype == 'chaos_poincare':
            return self.tr("plot_poincare")
        elif ptype == 'preprocessing':
            op = plot_data.get('operation', 'Unknown')
            return f"{self.tr('plot_preprocessing')}: {op}"
        elif ptype == 'embedding_2d':
            tau = plot_data.get('tau', '?')
            return f"2D Phase Space (τ={tau})"
        elif ptype == 'embedding_3d':
            tau = plot_data.get('tau', '?')
            return f"3D Phase Space (τ={tau})"
        elif ptype == 'return_map':
            return "Return Map"
        else:
            return f"{self.tr('plot_title')} ({ptype})"

    def _update_bottom_combo(self):
        """Dropdown menu'yu history'den guncelle"""
        # Mevcut secimi sakla
        current_text = self.bottom_combo.currentText()
        
        # Combobox'i temizle
        self.bottom_combo.blockSignals(True)
        self.bottom_combo.clear()
        self.bottom_combo.addItem(self.tr("plot_empty"))
        
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
        if index == 0:  # "(Boş)" / "(Empty)"
            self._clear_bottom_plot()
            return
        
        # History'den secilen grafigi bul (index-1 cunku ilk item "(Bos)")
        history_idx = len(self.plot_history) - index  # Ters sirada
        if 0 <= history_idx < len(self.plot_history):
            entry = self.plot_history[history_idx]
            ptype = entry['data'].get('type', '')
            
            if ptype == 'embedding_3d':
                # 3D widget'a gec
                self.bottom_stack.setCurrentIndex(1)
                self._plot_embedding_3d(entry['data'], self.bottom_3d_widget, self.bottom_title_label)
            else:
                # 2D widget'a gec
                self.bottom_stack.setCurrentIndex(0)
                # Color bar'ı gizle
                self.bottom_colorbar_label.hide()
                self._render_plot_to_widget(
                    entry['data'], 
                    self.bottom_plot_widget, 
                    self.bottom_title_label
                )
                # Auto-range
                self.bottom_plot_widget.autoRange()

    def _clear_bottom_plot(self):
        """Alt paneli temizle"""
        # 2D widget'a gec ve temizle
        self.bottom_stack.setCurrentIndex(0)
        # Color bar'ı gizle
        self.bottom_colorbar_label.hide()
        self.bottom_plot_widget.clear()
        self.bottom_title_label.setText(self.tr("plot_empty"))
        self.bottom_combo.blockSignals(True)
        self.bottom_combo.setCurrentIndex(0)
        self.bottom_combo.blockSignals(False)

    def _render_plot_to_widget(self, plot_data: dict, widget: pg.PlotWidget, title_label: QLabel):
        """Belirli bir plot_data'yi 2D widget'a ciz (3D haric)"""
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
        elif ptype == 'chaos_poincare':
            self._plot_poincare(plot_data, widget, title_label)
        elif ptype == 'chaos_bifurcation':
            self._plot_chaos_bifurcation(plot_data, widget, title_label)
        elif ptype == 'chaos_lyapunov_sweep':
            self._plot_chaos_lyapunov_sweep(plot_data, widget, title_label)
        elif ptype == 'preprocessing':
            self._plot_preprocessing(plot_data, widget, title_label)
        elif ptype == 'embedding_2d':
            self._plot_embedding_2d(plot_data, widget, title_label)
        elif ptype == 'return_map':
            self._plot_return_map(plot_data, widget, title_label)

    # ------------------------------------------------------------------
    # PLOT FUNCTIONS (her biri artik widget + title_label alir)
    # ------------------------------------------------------------------
    
    def _plot_timeseries(self, d, widget, title_label):
        widget.clear()
        widget.setLogMode(y=False)
        widget.setLabel('bottom', self.tr('plot_time'))
        # SI prefix'i kapat: "(x0.001)" gibi otomatik çarpan yazmasın
        widget.getAxis('left').enableAutoSIPrefix(False)
        widget.getAxis('bottom').enableAutoSIPrefix(False)

        meta = d.get('metadata', {}) or {}
        time = d['time']

        var_name = meta.get('output_var_name', '')
        y_label = f"{var_name}(t)" if var_name else self.tr('plot_value')
        widget.setLabel('left', y_label)
        title_label.setText(f"{self.tr('plot_time_series')} - {y_label}" if var_name else self.tr("plot_time_series"))
        widget.plot(time, d['data'], pen=self._get_pen(), name=y_label)

    def _plot_linear(self, d, widget, title_label):
        widget.clear()
        widget.setLogMode(y=False)
        atype = d.get('analysis_type', 'acf')
        results = d['results']
        n = d.get('n_data', 1000)

        if atype == 'acf':
            title_label.setText("ACF")
            widget.setLabel('left', 'ACF')
            widget.setLabel('bottom', self.tr('plot_lag'))
            widget.plot(results['lags'], results['acf'],
                        pen=self._get_pen())
            conf = 1.96 / np.sqrt(n)
            widget.plot(results['lags'], [conf] * len(results['lags']),
                        pen=pg.mkPen(color='red', style=Qt.DashLine))
            widget.plot(results['lags'], [-conf] * len(results['lags']),
                        pen=pg.mkPen(color='red', style=Qt.DashLine))
        elif atype == 'pacf':
            title_label.setText("PACF")
            widget.setLabel('left', 'PACF')
            widget.setLabel('bottom', self.tr('plot_lag'))
            widget.plot(results['lags'], results['pacf'],
                        pen=self._get_pen())
        elif atype == 'fft':
            title_label.setText(self.tr("plot_fft_power"))
            widget.setLabel('left', self.tr('plot_power'))
            widget.setLabel('bottom', self.tr('plot_frequency'))
            widget.plot(results['frequencies'], results['power'],
                        pen=self._get_pen())
            widget.setLogMode(y=True)

    def _plot_param_tau(self, d, widget, title_label):
        widget.clear()
        widget.setLogMode(y=False)
        title_label.setText(self.tr("plot_ami_delay"))
        widget.setLabel('left', 'AMI')
        widget.setLabel('bottom', self.tr('plot_lag'))
        results = d['results']
        widget.plot(results['lags'], results['ami'],
                    pen=self._get_pen())
        tau = results['tau']
        ami = results['ami']
        if 0 < tau <= len(ami):
            scatter_size = self.plot_settings.get('scatter_size')
            widget.plot([tau], [ami[tau - 1]],
                        pen=None, symbol='o', symbolSize=scatter_size * 2,
                        symbolBrush='red')

    def _plot_param_m(self, d, widget, title_label):
        widget.clear()
        widget.setLogMode(y=False)
        title_label.setText(self.tr("plot_fnn_dim"))
        widget.setLabel('left', 'FNN %')
        widget.setLabel('bottom', self.tr('plot_dimension'))
        results = d['results']
        widget.plot(results['dimensions'], results['fnn'],
                    pen=self._get_pen())
        widget.plot(results['dimensions'],
                    [1.0] * len(results['dimensions']),
                    pen=pg.mkPen(color='red', style=Qt.DashLine))

    def _plot_chaos_lyapunov(self, d, widget, title_label):
        widget.clear()
        widget.setLogMode(y=False)
        results = d['results']
        algo = results.get('algorithm', '')
        title_label.setText(f"{self.tr('plot_lyapunov')} - {algo}")

        if 't_steps' in results and 'divergence' in results:
            widget.setLabel('left', 'ln(divergence)')
            widget.setLabel('bottom', self.tr('plot_time'))
            t = results['t_steps']
            div = results['divergence']
            valid = ~np.isnan(div)
            widget.plot(t[valid], div[valid],
                        pen=self._get_pen())
        else:
            widget.setLabel('left', 'λ')
            widget.setLabel('bottom', '')
            lyap = results.get('lyapunov', 0)
            scatter_size = self.plot_settings.get('scatter_size')
            widget.plot([0], [lyap],
                        pen=None, symbol='o', symbolSize=scatter_size * 3,
                        symbolBrush=self.plot_settings.get('line_color'))

    def _plot_chaos_spectrum(self, d, widget, title_label):
        widget.clear()
        widget.setLogMode(y=False)
        title_label.setText(self.tr("plot_lyapunov_spectrum"))
        widget.setLabel('left', 'λ (nats/s)')
        widget.setLabel('bottom', self.tr('plot_exponent_index'))
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
        title_label.setText(self.tr("plot_correlation_dim"))
        widget.setLabel('left', 'log(C(r))')
        widget.setLabel('bottom', 'log(r)')
        results = d['results']
        radii = results['radii']
        c_r = results['c_r']
        valid = c_r > 0
        if np.any(valid):
            log_r = np.log(radii[valid])
            log_c = np.log(c_r[valid])
            scatter_size = self.plot_settings.get('scatter_size')
            widget.plot(log_r, log_c,
                        pen=self._get_pen(),
                        symbol='o', symbolSize=scatter_size)

    def _plot_chaos_bifurcation(self, d, widget, title_label):
        """Bifurcation diyagrami: x=parametre, y=sistem ornek noktalari (scatter)."""
        widget.clear()
        widget.setLogMode(y=False)
        sys_name = d.get('system', '?')
        sweep_p = d.get('sweep_param', '?')
        title_label.setText(f"Bifurcation: {sys_name} ({sweep_p})")
        widget.setLabel('left', 'sample value')
        widget.setLabel('bottom', sweep_p)

        sweep_results = d.get('sweep_results', [])  # [(param_val, samples_array), ...]
        if not sweep_results:
            return

        # Tum noktalari tek scatter'a topla
        xs = []
        ys = []
        for param_val, samples in sweep_results:
            if len(samples) == 0:
                continue
            xs.extend([param_val] * len(samples))
            ys.extend(samples.tolist())

        if not xs:
            return

        scatter = pg.ScatterPlotItem(
            x=xs, y=ys,
            size=2,
            pen=None,
            brush=pg.mkBrush(self.plot_settings.get('line_color')),
        )
        widget.addItem(scatter)

    def _plot_chaos_lyapunov_sweep(self, d, widget, title_label):
        """Lyapunov sweep: x=parametre, y=lambda1 (line + sifir cizgisi)."""
        widget.clear()
        widget.setLogMode(y=False)
        sys_name = d.get('system', '?')
        sweep_p = d.get('sweep_param', '?')
        method = d.get('method', '?')
        title_label.setText(f"Lyapunov sweep: {sys_name} ({sweep_p}, {method})")
        widget.setLabel('left', 'λ₁')
        widget.setLabel('bottom', sweep_p)

        sweep_results = d.get('sweep_results', [])  # [(param_val, lambda1), ...]
        if not sweep_results:
            return

        xs = np.array([p for p, _ in sweep_results], dtype=float)
        ys = np.array([l for _, l in sweep_results], dtype=float)
        valid = ~np.isnan(ys)
        if not np.any(valid):
            return

        # Sifir referans cizgisi (kaos / stabil sinir)
        widget.addLine(y=0, pen=pg.mkPen('#888888', width=1, style=Qt.DashLine))
        # Lambda1 egrisi + noktalar
        scatter_size = self.plot_settings.get('scatter_size')
        widget.plot(xs[valid], ys[valid],
                    pen=self._get_pen(),
                    symbol='o', symbolSize=scatter_size,
                    symbolBrush=self.plot_settings.get('line_color'))

    def _plot_poincare(self, d, widget, title_label):
        """Poincaré kesiti scatter grafiği."""
        widget.clear()
        widget.setLogMode(y=False)
        plane = d.get('plane', {})
        axis = plane.get('axis', 0)
        value = plane.get('value', 0.0)
        title_label.setText(f"{self.tr('plot_poincare')}  (eksen {axis} = {value:.4g})")

        crossings = d.get('crossings', np.empty((0, 2)))
        if len(crossings) == 0:
            widget.setLabel('left', '')
            widget.setLabel('bottom', '')
            return

        m = d.get('m', crossings.shape[1] if crossings.ndim == 2 else 2)

        # Kesit ekseni dışında ilk iki ekseni göster
        plot_axes = [i for i in range(crossings.shape[1]) if i != axis]
        if len(plot_axes) < 2:
            # m=1 veya kesit tüm boyutları tüketmişse: x vs index
            x_data = np.arange(len(crossings))
            y_data = crossings[:, 0]
            widget.setLabel('left', f'x(t-{0}τ)')
            widget.setLabel('bottom', 'Crossing index')
        else:
            ax0, ax1 = plot_axes[0], plot_axes[1]
            x_data = crossings[:, ax0]
            y_data = crossings[:, ax1]
            widget.setLabel('left', f'x(t-{ax1}τ)')
            widget.setLabel('bottom', f'x(t-{ax0}τ)')

        scatter_size = self.plot_settings.get('scatter_size')
        color = self.plot_settings.get('line_color')
        widget.plot(
            x_data, y_data,
            pen=None, symbol='o',
            symbolSize=max(2, scatter_size - 2),
            symbolBrush=color,
            symbolPen=None,
        )

    def _plot_preprocessing(self, d, widget, title_label):
        widget.clear()
        widget.setLogMode(y=False)
        title_label.setText(f"{self.tr('plot_preprocessing')} - {d.get('operation', '')}")
        widget.setLabel('left', self.tr('plot_value'))
        widget.setLabel('bottom', self.tr('plot_time'))

        # Orijinal veri (soluk)
        if d.get('data_original') is not None:
            widget.plot(d['time_original'], d['data_original'],
                        pen=pg.mkPen(color='#555555', width=1),
                        name=self.tr('plot_original'))
        # Islenmis veri
        widget.plot(d['time_processed'], d['data_processed'],
                    pen=self._get_pen(),
                    name=self.tr('plot_processed'))

    def _plot_embedding_2d(self, d, widget, title_label):
        """2D Faz Uzayı: x(t) vs x(t+τ)"""
        widget.clear()
        widget.setLogMode(y=False)
        tau = d.get('tau', '?')
        title_label.setText(f"2D Phase Space (τ={tau})")
        widget.setLabel('left', f'x(t+{tau})')
        widget.setLabel('bottom', 'x(t)')
        
        x = d['x']
        y = d['y']
        
        # Scatter plot (trajectory)
        widget.plot(x, y, pen=self._get_pen())
        
        # İlk nokta (başlangıç) kırmızı
        widget.plot([x[0]], [y[0]], 
                    pen=None, symbol='o', symbolSize=8, 
                    symbolBrush='#dc322f', name=self.tr('plot_start'))
        
        # Son nokta (bitiş) yeşil
        widget.plot([x[-1]], [y[-1]], 
                    pen=None, symbol='s', symbolSize=8, 
                    symbolBrush='#859900', name=self.tr('plot_end'))

    def _plot_embedding_3d(self, d, widget, title_label):
        """3D Faz Uzayı: x(t), x(t+τ), x(t+2τ) - Gerçek 3D görselleştirme"""
        tau = d.get('tau', '?')
        title_label.setText(
            f"3D Phase Space (τ={tau}) | "
            f"Color: Blue (start) → Red (end) = time flow"
        )
        
        x = d['x']
        y = d['y']
        z = d.get('z')
        
        if z is None:
            return
        
        # Widget'ı temizle (tüm item'ları kaldır)
        widget.clear()
        
        # Color bar'ı göster (hangi panel olduğunu kontrol et)
        if widget == self.top_3d_widget:
            self.top_colorbar_label.show()
            self.top_colorbar_label.raise_()
            # Pozisyonu ayarla (sağ alt köşe)
            parent = self.top_colorbar_label.parent()
            self.top_colorbar_label.move(
                parent.width() - self.top_colorbar_label.width() - 10,
                parent.height() - self.top_colorbar_label.height() - 10
            )
        elif widget == self.bottom_3d_widget:
            self.bottom_colorbar_label.show()
            self.bottom_colorbar_label.raise_()
            parent = self.bottom_colorbar_label.parent()
            self.bottom_colorbar_label.move(
                parent.width() - self.bottom_colorbar_label.width() - 10,
                parent.height() - self.bottom_colorbar_label.height() - 10
            )
        
        # 3D koordinatlar (numpy array olarak)
        pos = np.column_stack([x, y, z])
        
        # Renk gradient: zaman ilerledikçe mavi -> kırmızı
        n = len(x)
        colors = np.zeros((n, 4))
        colors[:, 0] = np.linspace(0, 1, n)  # Kırmızı artıyor
        colors[:, 2] = np.linspace(1, 0, n)  # Mavi azalıyor
        colors[:, 3] = 0.6  # Alpha (yarı saydam)
        
        # Scatter plot (3D noktalar) - settings'den boyut al
        scatter_3d_size = self.plot_settings.get('scatter_3d_size')
        scatter = gl.GLScatterPlotItem(
            pos=pos,
            color=colors,
            size=scatter_3d_size,
            pxMode=True  # Piksel cinsinden boyut
        )
        widget.addItem(scatter)
        
        # Trajectory line (çizgi) - settings'den kalınlık al
        trajectory_width = self.plot_settings.get('trajectory_3d_width')
        antialiasing = self.plot_settings.get('antialiasing')
        line = gl.GLLinePlotItem(
            pos=pos,
            color=(0.5, 0.5, 0.5, 0.3),  # Gri, çok saydam
            width=trajectory_width,
            antialias=antialiasing
        )
        widget.addItem(line)
        
        # Başlangıç noktası (büyük kırmızı nokta)
        start_pos = np.array([pos[0]])
        start_scatter = gl.GLScatterPlotItem(
            pos=start_pos,
            color=(1, 0, 0, 1),  # Kırmızı
            size=10,
            pxMode=True
        )
        widget.addItem(start_scatter)
        
        # Bitiş noktası (büyük yeşil nokta)
        end_pos = np.array([pos[-1]])
        end_scatter = gl.GLScatterPlotItem(
            pos=end_pos,
            color=(0, 1, 0, 1),  # Yeşil
            size=10,
            pxMode=True
        )
        widget.addItem(end_scatter)
        
        # Grid (referans için)
        grid = gl.GLGridItem()
        grid.scale(
            (x.max() - x.min()) / 10,
            (y.max() - y.min()) / 10,
            (z.max() - z.min()) / 10
        )
        # Grid'i ortala
        grid.translate(
            (x.max() + x.min()) / 2,
            (y.max() + y.min()) / 2,
            z.min()
        )
        widget.addItem(grid)
        
        # Kamera ayarları (iyi bir başlangıç açısı)
        widget.setCameraPosition(distance=np.ptp(pos) * 2.5)

    def _plot_return_map(self, d, widget, title_label):
        """Geri Dönüş Haritası: x(t) vs x(t+1)"""
        widget.clear()
        widget.setLogMode(y=False)
        title_label.setText("Return Map")
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
                    name=self.tr('plot_diagonal'))

    # ------------------------------------------------------------------
    # ADIM SEKME SİSTEMİ (üst panel)
    # ------------------------------------------------------------------

    def _update_step_tabs(self, step: int, new_plot_data: dict):
        """Bir adıma yeni plot ekler/günceller ve sekme çubuğunu yeniler."""
        if step not in self._step_plots:
            self._step_plots[step] = []

        ptype = new_plot_data.get('type')
        existing = self._step_plots[step]
        found_idx = None
        for i, p in enumerate(existing):
            if p.get('type') == ptype:
                existing[i] = new_plot_data
                found_idx = i
                break
        if found_idx is None:
            existing.append(new_plot_data)
            found_idx = len(existing) - 1

        # En son eklenen/güncellenen sekme aktif
        self._active_tab_per_step[step] = found_idx

        # Şu an bu adımdaysak sekme çubuğunu güncelle
        if self._current_tab_step == step:
            self._show_top_tabs_for_step(step)

    def on_step_changed(self, step: int):
        """ContentPanel adım değiştirdiğinde çağrılır — sekme çubuğunu günceller."""
        self._current_tab_step = step
        self._show_top_tabs_for_step(step)

    def _show_top_tabs_for_step(self, step: int):
        """Verilen adıma ait sekme butonlarını oluşturur/günceller."""
        plots = self._step_plots.get(step, [])

        # Mevcut butonları temizle
        for btn in self.top_tab_buttons:
            btn.setParent(None)
        self.top_tab_buttons = []
        while self.top_tab_layout.count():
            item = self.top_tab_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        if len(plots) < 2:
            self.top_tab_row.setVisible(False)
            return

        self.top_tab_row.setVisible(True)
        active_idx = self._active_tab_per_step.get(step, 0)

        for i, plot_data in enumerate(plots):
            title = self._generate_title(plot_data)
            btn = QPushButton(title)
            btn.setCheckable(True)
            btn.setChecked(i == active_idx)
            self._style_tab_button(btn, i == active_idx)
            btn.clicked.connect(
                lambda checked, s=step, idx=i: self._on_top_tab_clicked(s, idx)
            )
            self.top_tab_layout.addWidget(btn)
            self.top_tab_buttons.append(btn)

        self.top_tab_layout.addStretch()

    def _on_top_tab_clicked(self, step: int, idx: int):
        """Kullanıcı bir sekmeye tıkladığında ilgili grafiği gösterir."""
        self._active_tab_per_step[step] = idx

        # Buton stillerini güncelle
        for i, btn in enumerate(self.top_tab_buttons):
            btn.setChecked(i == idx)
            self._style_tab_button(btn, i == idx)

        # Seçilen grafiği çiz
        plots = self._step_plots.get(step, [])
        if idx < len(plots):
            plot_data = plots[idx]
            ptype = plot_data.get('type', '')
            if ptype == 'embedding_3d':
                self.top_stack.setCurrentIndex(1)
                self._plot_embedding_3d(plot_data, self.top_3d_widget, self.top_title_label)
            else:
                self.top_stack.setCurrentIndex(0)
                self.top_colorbar_label.hide()
                self._render_plot_to_widget(plot_data, self.top_plot_widget, self.top_title_label)
                self.top_plot_widget.autoRange()

    def _style_tab_button(self, btn: QPushButton, active: bool):
        """Sekme butonuna aktif/pasif stilini uygular."""
        if active:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #0e639c;
                    color: #ffffff;
                    border: 1px solid #4d8cc4;
                    border-radius: 4px;
                    padding: 3px 12px;
                    font-size: 9pt;
                    font-weight: bold;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a;
                    color: #909090;
                    border: 1px solid #3f3f3f;
                    border-radius: 4px;
                    padding: 3px 12px;
                    font-size: 9pt;
                }
                QPushButton:hover {
                    background-color: #333333;
                    color: #c0c0c0;
                    border: 1px solid #555555;
                }
            """)

    def invalidate_steps(self, steps: list):
        """Belirtilen adımların sekme verilerini siler (ör. ön işleme sonrası)."""
        for step in steps:
            self._step_plots.pop(step, None)
            self._active_tab_per_step.pop(step, None)
        if self._current_tab_step in steps:
            self.top_tab_row.setVisible(False)
            self.top_tab_buttons = []

    # ------------------------------------------------------------------
    def update_plot_theme(self):
        self._apply_theme(self.top_plot_widget)
        self._apply_theme(self.bottom_plot_widget)

    def refresh_ui(self):
        """Dil değiştiğinde görünür metinleri ve mevcut menüleri yenile."""
        self.top_title_label.setText(self.tr("plot_title"))
        self.bottom_compare_label.setText(self.tr("plot_compare_label"))
        self.clear_bottom_btn.setText(self.tr("plot_clear"))

        self.bottom_combo.blockSignals(True)
        if self.bottom_combo.count() > 0:
            self.bottom_combo.setItemText(0, self.tr("plot_empty"))
        self.bottom_combo.blockSignals(False)

        if self.bottom_title_label.text() in {"(Bos)", "(Boş)", "(Empty)"}:
            self.bottom_title_label.setText(self.tr("plot_empty"))
        if self.top_title_label.text() in {"Grafik", "Plot"}:
            self.top_title_label.setText(self.tr("plot_title"))

        if self._current_tab_step >= 0:
            self._show_top_tabs_for_step(self._current_tab_step)

    def _apply_theme(self, pw: pg.PlotWidget):
        theme = self.theme_manager.get_theme()
        pw.setBackground(theme.colors['plot_bg'])
        for axis in ['left', 'bottom', 'right', 'top']:
            ax = pw.getAxis(axis)
            ax.setPen(pg.mkPen(color=theme.colors['plot_text'], width=1))
            ax.setTextPen(pg.mkPen(color=theme.colors['plot_text']))
    
    def _apply_theme_3d(self, glview: gl.GLViewWidget):
        """3D widget icin tema uygula"""
        theme = self.theme_manager.get_theme()
        # Arka plan rengi (RGB tuple olarak)
        bg_hex = theme.colors['plot_bg']
        if bg_hex.startswith('#'):
            r = int(bg_hex[1:3], 16) / 255.0
            g = int(bg_hex[3:5], 16) / 255.0
            b = int(bg_hex[5:7], 16) / 255.0
            glview.setBackgroundColor((r, g, b, 1.0))
    
    def _create_colorbar_label(self):
        """Sabit 2D color bar overlay (sag alt kose, yatay gradient)"""
        from PySide6.QtGui import QLinearGradient, QPainter, QPixmap
        from PySide6.QtCore import QRect, QPoint
        
        label = QLabel()
        label.setFixedSize(200, 40)  # Genislik x Yukseklik
        
        # Gradient pixmap olustur (mavi -> kirmizi, soldan saga)
        pixmap = QPixmap(200, 40)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        
        # Gradient bar (ust 20 piksel)
        gradient = QLinearGradient(0, 0, 200, 0)  # Yatay (soldan saga)
        gradient.setColorAt(0.0, Qt.blue)
        gradient.setColorAt(1.0, Qt.red)
        
        painter.setBrush(gradient)
        painter.setPen(Qt.white)
        painter.drawRect(0, 0, 199, 15)
        
        # Metin etiketleri
        painter.setPen(Qt.white)
        painter.drawText(5, 32, "t=0 (start)")
        painter.drawText(120, 32, "t=end")
        
        painter.end()
        
        label.setPixmap(pixmap)
        label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 150);
            border-radius: 5px;
            padding: 5px;
        """)
        
        return label
