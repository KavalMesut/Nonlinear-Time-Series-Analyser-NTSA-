"""
Content panel - right side showing data and plots
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QTextEdit, QStackedWidget
)
from PySide6.QtCore import Qt
import pyqtgraph as pg
import numpy as np

from .data_load_panel import DataLoadPanel
from .linear_analysis_panel import LinearAnalysisPanel
from .parameter_estimation_panel import ParameterEstimationPanel
from .chaos_analysis_panel import ChaosAnalysisPanel


class ContentPanel(QWidget):
    """Right panel showing content"""
    
    def __init__(self, translation_manager, theme_manager):
        super().__init__()
        self.tm = translation_manager
        self.theme_manager = theme_manager
        self.current_data = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Stacked widget for different steps
        self.stacked_widget = QStackedWidget()
        
        # Step 1: Data Loading
        self.data_load_panel = DataLoadPanel(self.tm)
        self.data_load_panel.data_loaded.connect(self.on_data_loaded)
        self.stacked_widget.addWidget(self.data_load_panel)
        
        # Step 2: Preprocessing (placeholder)
        placeholder2 = QLabel("Step 2: Preprocessing\n\nComing soon...")
        placeholder2.setAlignment(Qt.AlignCenter)
        self.stacked_widget.addWidget(placeholder2)
        
        # Step 3: Linear Analysis
        self.linear_analysis_panel = LinearAnalysisPanel(self.tm, self.theme_manager)
        self.linear_analysis_panel.analysis_complete.connect(self.on_linear_analysis_complete)
        self.stacked_widget.addWidget(self.linear_analysis_panel)
        
        # Step 4: Parameter Estimation
        self.parameter_panel = ParameterEstimationPanel(self.tm, self.theme_manager)
        self.parameter_panel.parameters_estimated.connect(self.on_parameters_estimated)
        self.stacked_widget.addWidget(self.parameter_panel)
        
        # Step 5: Embedding (placeholder)
        placeholder5 = QLabel("Step 5: Embedding Visualization\n\nComing soon...")
        placeholder5.setAlignment(Qt.AlignCenter)
        self.stacked_widget.addWidget(placeholder5)
        
        # Step 6: Chaos Analysis
        self.chaos_panel = ChaosAnalysisPanel(self.tm, self.theme_manager)
        self.chaos_panel.analysis_complete.connect(self.on_chaos_analysis_complete)
        self.stacked_widget.addWidget(self.chaos_panel)
        
        # Step 7: Results (placeholder)
        placeholder7 = QLabel("Step 7: Results Summary\n\nComing soon...")
        placeholder7.setAlignment(Qt.AlignCenter)
        self.stacked_widget.addWidget(placeholder7)
        
        layout.addWidget(self.stacked_widget)
        
        # Tab widget for plots and results
        self.tabs = QTabWidget()
        
        # Data info tab
        self.data_info = QTextEdit()
        self.data_info.setReadOnly(True)
        self.data_info.setMaximumHeight(200)
        self.tabs.addTab(self.data_info, self.tm('step_data_load'))
        
        # Time series plot
        self.plot_widget = self.create_plot_widget()
        self.tabs.addTab(self.plot_widget, "Time Series")
        
        layout.addWidget(self.tabs)
    
    def create_plot_widget(self):
        """Create PyQtGraph plot widget"""
        plot_widget = pg.PlotWidget()
        
        # Configure plot with dark theme
        self.update_plot_theme(plot_widget)
        
        # Configure axes
        plot_widget.setLabel('left', 'Value')
        plot_widget.setLabel('bottom', 'Time')
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
        plot_widget.addLegend()
        
        return plot_widget
    
    def on_data_loaded(self, timeseries):
        """Handle data loaded event"""
        self.current_data = timeseries
        
        # Update info
        info_text = f"Data loaded successfully!\n\n"
        info_text += f"Length: {len(timeseries)} points\n"
        info_text += f"Time step (dt): {timeseries.dt}\n"
        info_text += f"Total time: {len(timeseries) * timeseries.dt:.2f}\n"
        info_text += f"Mean: {np.mean(timeseries.data):.4f}\n"
        info_text += f"Std: {np.std(timeseries.data):.4f}\n"
        info_text += f"Min: {np.min(timeseries.data):.4f}\n"
        info_text += f"Max: {np.max(timeseries.data):.4f}\n"
        
        if timeseries.metadata:
            info_text += f"\nMetadata:\n"
            for key, value in timeseries.metadata.items():
                info_text += f"  {key}: {value}\n"
        
        self.data_info.setText(info_text)
        
        # Plot data
        self.plot_widget.clear()
        time = timeseries.time
        self.plot_widget.plot(time, timeseries.data, pen=pg.mkPen(color='#0e639c', width=1.5), name='Time Series')
        
        # Switch to plot tab
        self.tabs.setCurrentIndex(1)
        
        # Unlock next steps
        main_window = self.window()
        if hasattr(main_window, 'steps_panel'):
            main_window.steps_panel.unlock_step(1)
            main_window.steps_panel.unlock_step(2)
        
        # Pass data to analysis panels
        self.linear_analysis_panel.set_data(timeseries)
        self.parameter_panel.set_data(timeseries)
    
    def on_linear_analysis_complete(self, results):
        """Handle linear analysis completion"""
        # Unlock parameter estimation
        main_window = self.window()
        if hasattr(main_window, 'steps_panel'):
            main_window.steps_panel.unlock_step(3)
    
    def on_parameters_estimated(self, params):
        """Handle parameter estimation completion"""
        if 'tau' in params and 'm' in params:
            tau = params['tau']
            m = params['m']
            
            # Unlock embedding and chaos analysis
            main_window = self.window()
            if hasattr(main_window, 'steps_panel'):
                main_window.steps_panel.unlock_step(4)
                main_window.steps_panel.unlock_step(5)
            
            # Pass parameters to chaos analysis
            self.chaos_panel.set_data(self.current_data, tau, m)
    
    def on_chaos_analysis_complete(self, results):
        """Handle chaos analysis completion"""
        # Unlock results
        main_window = self.window()
        if hasattr(main_window, 'steps_panel'):
            main_window.steps_panel.unlock_step(6)
    
    def set_step(self, step_index):
        """Set current step"""
        self.stacked_widget.setCurrentIndex(step_index)
    
    def update_plot_theme(self, plot_widget=None):
        """Update plot colors based on theme"""
        if plot_widget is None:
            plot_widget = self.plot_widget
        
        theme = self.theme_manager.get_theme()
        
        # Set background
        plot_widget.setBackground(theme.colors['plot_bg'])
        
        # Set axis colors
        for axis in ['left', 'bottom', 'right', 'top']:
            ax = plot_widget.getAxis(axis)
            ax.setPen(pg.mkPen(color=theme.colors['plot_text'], width=1))
            ax.setTextPen(pg.mkPen(color=theme.colors['plot_text']))
        
        # Set grid color
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
    
    def refresh_ui(self):
        """Refresh UI with current language"""
        # Update tab labels
        self.tabs.setTabText(0, self.tm('step_data_load'))
        self.data_load_panel.refresh_ui()
        self.linear_analysis_panel.refresh_ui()
        self.parameter_panel.refresh_ui()
        self.chaos_panel.refresh_ui()
