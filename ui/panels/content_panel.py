"""
Content panel — orta panel, analiz adimina gore kontrolleri gosterir.
Grafik PlotPanel'de (sag panel).
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QStackedWidget, QScrollArea
)
from PySide6.QtCore import Qt, Signal
import numpy as np

from .data_load_panel import DataLoadPanel
from .linear_analysis_panel import LinearAnalysisPanel
from .parameter_estimation_panel import ParameterEstimationPanel
from .chaos_analysis_panel import ChaosAnalysisPanel


class ContentPanel(QWidget):
    """Orta panel — kontrol ve veri panelleri (grafik yok)"""
    
    # PlotPanel'e iletilecek sinyaller
    plot_requested = Signal(dict)
    
    def __init__(self, translation_manager, theme_manager):
        super().__init__()
        self.tm = translation_manager
        self.theme_manager = theme_manager
        self.current_data = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Stacked widget — her adim icin bir sayfa
        self.stacked_widget = QStackedWidget()
        
        # 0 — Data Loading
        self.data_load_panel = DataLoadPanel(self.tm)
        self.data_load_panel.data_loaded.connect(self.on_data_loaded)
        self.stacked_widget.addWidget(self.data_load_panel)
        
        # 1 — Preprocessing (placeholder)
        placeholder2 = QLabel("Step 2: Preprocessing\n\nComing soon...")
        placeholder2.setAlignment(Qt.AlignCenter)
        self.stacked_widget.addWidget(placeholder2)
        
        # 2 — Linear Analysis
        self.linear_analysis_panel = LinearAnalysisPanel(self.tm)
        self.linear_analysis_panel.analysis_complete.connect(self.on_linear_analysis_complete)
        self.linear_analysis_panel.plot_requested.connect(self._forward_plot)
        self.stacked_widget.addWidget(self.linear_analysis_panel)
        
        # 3 — Parameter Estimation
        self.parameter_panel = ParameterEstimationPanel(self.tm)
        self.parameter_panel.parameters_estimated.connect(self.on_parameters_estimated)
        self.parameter_panel.plot_requested.connect(self._forward_plot)
        self.stacked_widget.addWidget(self.parameter_panel)
        
        # 4 — Embedding (placeholder)
        placeholder5 = QLabel("Step 5: Embedding Visualization\n\nComing soon...")
        placeholder5.setAlignment(Qt.AlignCenter)
        self.stacked_widget.addWidget(placeholder5)
        
        # 5 — Chaos Analysis
        self.chaos_panel = ChaosAnalysisPanel(self.tm)
        self.chaos_panel.analysis_complete.connect(self.on_chaos_analysis_complete)
        self.chaos_panel.plot_requested.connect(self._forward_plot)
        self.stacked_widget.addWidget(self.chaos_panel)
        
        # 6 — Results (placeholder)
        placeholder7 = QLabel("Step 7: Results Summary\n\nComing soon...")
        placeholder7.setAlignment(Qt.AlignCenter)
        self.stacked_widget.addWidget(placeholder7)
        
        layout.addWidget(self.stacked_widget)
    
    def _forward_plot(self, plot_data: dict):
        """Sub-panellerden gelen grafik istegini PlotPanel'e ilet"""
        self.plot_requested.emit(plot_data)
    
    def on_data_loaded(self, timeseries):
        self.current_data = timeseries
        
        # PlotPanel'e zaman serisi grafigi gonder
        self.plot_requested.emit({
            'type': 'timeseries',
            'time': timeseries.time,
            'data': timeseries.data,
            'metadata': timeseries.metadata
        })
        
        # Adimlari ac
        main_window = self.window()
        if hasattr(main_window, 'steps_panel'):
            main_window.steps_panel.unlock_step(1)
            main_window.steps_panel.unlock_step(2)
        
        self.linear_analysis_panel.set_data(timeseries)
        self.parameter_panel.set_data(timeseries)
    
    def on_linear_analysis_complete(self, results):
        main_window = self.window()
        if hasattr(main_window, 'steps_panel'):
            main_window.steps_panel.unlock_step(3)
    
    def on_parameters_estimated(self, params):
        if 'tau' in params and 'm' in params:
            tau = params['tau']
            m = params['m']
            main_window = self.window()
            if hasattr(main_window, 'steps_panel'):
                main_window.steps_panel.unlock_step(4)
                main_window.steps_panel.unlock_step(5)
            self.chaos_panel.set_data(self.current_data, tau, m)
    
    def on_chaos_analysis_complete(self, results):
        main_window = self.window()
        if hasattr(main_window, 'steps_panel'):
            main_window.steps_panel.unlock_step(6)
    
    def set_step(self, step_index):
        self.stacked_widget.setCurrentIndex(step_index)
    
    def update_plot_theme(self):
        """Artik grafik yok, PlotPanel guncellenecek"""
        pass
    
    def refresh_ui(self):
        self.data_load_panel.refresh_ui()
        self.linear_analysis_panel.refresh_ui()
        self.parameter_panel.refresh_ui()
        self.chaos_panel.refresh_ui()
