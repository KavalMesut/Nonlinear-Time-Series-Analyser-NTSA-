"""
Embedding visualization panel — phase space reconstruction görselleştirmesi.
2D phase space, 3D phase space, return map.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QSpinBox, QComboBox, QFormLayout
)
from PySide6.QtCore import Signal
import numpy as np

from analysis.embedding import embed_timeseries


class EmbeddingPanel(QWidget):
    """Embedding görselleştirme paneli"""
    
    plot_requested = Signal(dict)
    embedding_complete = Signal(dict)  # tau, m bilgisini gönder
    
    def __init__(self, translation_manager):
        super().__init__()
        self.tm = translation_manager
        self.current_data = None
        self.tau = None
        self.m = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Başlık
        title = QLabel(self.tm("embed_title"))
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title)
        
        # Açıklama
        desc = QLabel(
            "Zaman gecikmeli gömme ile oluşturulan faz uzayını görselleştirin.\n"
            "τ ve m parametreleri Step 4'ten otomatik gelir."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Parametreler grubu
        param_group = QGroupBox(self.tm("embed_params"))
        param_layout = QFormLayout()
        
        self.tau_label = QLabel("τ = ?")
        self.tau_label.setStyleSheet("font-weight: bold; color: #268bd2;")
        param_layout.addRow("Gecikme Süresi (τ):", self.tau_label)
        
        self.m_label = QLabel("m = ?")
        self.m_label.setStyleSheet("font-weight: bold; color: #268bd2;")
        param_layout.addRow("Gömme Boyutu (m):", self.m_label)
        
        # Manuel override (opsiyonel)
        self.manual_tau_spin = QSpinBox()
        self.manual_tau_spin.setRange(1, 100)
        self.manual_tau_spin.setValue(10)
        self.manual_tau_spin.setEnabled(False)
        self.manual_tau_spin.setButtonSymbols(QSpinBox.UpDownArrows)
        param_layout.addRow("Manuel τ:", self.manual_tau_spin)
        
        self.manual_m_spin = QSpinBox()
        self.manual_m_spin.setRange(2, 10)
        self.manual_m_spin.setValue(3)
        self.manual_m_spin.setEnabled(False)
        self.manual_m_spin.setButtonSymbols(QSpinBox.UpDownArrows)
        param_layout.addRow("Manuel m:", self.manual_m_spin)
        
        self.use_manual_check = QPushButton(self.tm("embed_manual"))
        self.use_manual_check.setCheckable(True)
        self.use_manual_check.toggled.connect(self._toggle_manual)
        param_layout.addRow("", self.use_manual_check)
        
        param_group.setLayout(param_layout)
        layout.addWidget(param_group)
        
        # Görselleştirme seçenekleri
        vis_group = QGroupBox(self.tm("embed_visualization"))
        vis_layout = QVBoxLayout()
        
        # 2D Phase Space
        btn_2d = QPushButton(self.tm("embed_2d"))
        btn_2d.clicked.connect(self._plot_2d_phase_space)
        vis_layout.addWidget(btn_2d)
        
        # 3D Phase Space
        btn_3d = QPushButton(self.tm("embed_3d"))
        btn_3d.clicked.connect(self._plot_3d_phase_space)
        vis_layout.addWidget(btn_3d)
        
        # Return Map
        btn_return = QPushButton(self.tm("embed_return"))
        btn_return.clicked.connect(self._plot_return_map)
        vis_layout.addWidget(btn_return)
        
        # Multi-dimensional projection (opsiyonel)
        btn_multi = QPushButton(self.tm("embed_multi"))
        btn_multi.clicked.connect(self._plot_multi_dim)
        btn_multi.setEnabled(False)  # Gelecekte eklenecek
        vis_layout.addWidget(btn_multi)
        
        vis_group.setLayout(vis_layout)
        layout.addWidget(vis_group)
        
        # Bilgi
        info = QLabel(
            "<b>Not:</b> 3D görselleştirme için OpenGL gereklidir. "
            "Eğer 3D grafik göremiyorsanız PyOpenGL yükleyin: <code>pip install PyOpenGL</code>"
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #b58900; padding: 8px; background-color: rgba(181, 137, 0, 0.1);")
        layout.addWidget(info)
        
        layout.addStretch()
    
    def set_data(self, timeseries, tau=None, m=None):
        """Veri ve parametreleri set et"""
        self.current_data = timeseries
        self.tau = tau
        self.m = m
        
        if tau:
            self.tau_label.setText(f"τ = {tau}")
            self.manual_tau_spin.setValue(tau)
        else:
            self.tau_label.setText("τ = ? (Step 4'ten hesaplayın)")
        
        if m:
            self.m_label.setText(f"m = {m}")
            self.manual_m_spin.setValue(m)
        else:
            self.m_label.setText("m = ? (Step 4'ten hesaplayın)")
    
    def _toggle_manual(self, checked):
        """Manuel parametre override toggle"""
        self.manual_tau_spin.setEnabled(checked)
        self.manual_m_spin.setEnabled(checked)
    
    def _get_params(self):
        """Aktif tau ve m değerlerini al"""
        if self.use_manual_check.isChecked():
            tau = self.manual_tau_spin.value()
            m = self.manual_m_spin.value()
        else:
            tau = self.tau
            m = self.m
        return tau, m
    
    def _plot_2d_phase_space(self):
        """2D faz uzayı plot (x(t) vs x(t+τ))"""
        if self.current_data is None:
            return
        
        tau, m = self._get_params()
        if tau is None:
            return
        
        data = self.current_data.data
        
        # Embedding: m=2 için
        embedded = embed_timeseries(data, m=2, tau=tau)
        
        # Plot data hazırla
        plot_data = {
            'type': 'embedding_2d',
            'x': embedded[:, 0],
            'y': embedded[:, 1],
            'tau': tau,
            'title': f'2D Faz Uzayı (τ={tau})'
        }
        
        self.plot_requested.emit(plot_data)
        
        # Emit embedding complete with tau, m
        self.embedding_complete.emit({'tau': tau, 'm': m if m else 2})
        
        # Mark phase space step as completed
        main_window = self.window()
        if hasattr(main_window, 'steps_panel'):
            main_window.steps_panel.mark_step_completed(4)  # Phase space completed
    
    def _plot_3d_phase_space(self):
        """3D faz uzayı plot (x(t), x(t+τ), x(t+2τ))"""
        if self.current_data is None:
            return
        
        tau, m = self._get_params()
        if tau is None or m is None:
            return
        
        if m < 3:
            m = 3  # En az 3 boyut gerekli
        
        data = self.current_data.data
        
        # Embedding: m=3 için
        embedded = embed_timeseries(data, m=3, tau=tau)
        
        # Plot data hazırla
        plot_data = {
            'type': 'embedding_3d',
            'x': embedded[:, 0],
            'y': embedded[:, 1],
            'z': embedded[:, 2],
            'tau': tau,
            'title': f'3D Faz Uzayı (τ={tau})'
        }
        
        self.plot_requested.emit(plot_data)
        
        # Emit embedding complete with tau, m
        self.embedding_complete.emit({'tau': tau, 'm': m})
    
    def _plot_return_map(self):
        """Geri dönüş haritası: x(t) vs x(t+1)"""
        if self.current_data is None:
            return
        
        tau, m = self._get_params()
        
        data = self.current_data.data
        
        # x(t) vs x(t+1)
        x_t = data[:-1]
        x_t1 = data[1:]
        
        # Plot data hazırla
        plot_data = {
            'type': 'return_map',
            'x': x_t,
            'y': x_t1,
            'title': 'Geri Dönüş Haritası (x(t) vs x(t+1))'
        }
        
        self.plot_requested.emit(plot_data)
        
        # Emit embedding complete with tau, m
        if tau and m:
            self.embedding_complete.emit({'tau': tau, 'm': m})
    
    def _plot_multi_dim(self):
        """Çok-boyutlu izdüşüm (gelecekte eklenecek)"""
        # PCA veya t-SNE ile yüksek boyutlu embedding'i 2D'ye indirgeme
        pass
    
    def refresh_ui(self):
        """UI'yi yenile (dil değişikliği için)"""
        # TODO: Çeviriler eklenecek
        pass
