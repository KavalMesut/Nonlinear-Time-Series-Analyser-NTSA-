"""
Plot settings manager for graph customization
"""
import json
from pathlib import Path
from PySide6.QtGui import QColor


class PlotSettings:
    """Manages plot visualization settings"""
    
    # Default settings
    DEFAULTS = {
        # Line settings
        'line_color': '#00AAFF',  # Cyan-blue
        'line_width': 2,  # 1-5 px
        
        # Scatter settings
        'scatter_size': 5,  # 2-10 px
        'scatter_color': '#00AAFF',
        
        # Grid settings
        'grid_alpha': 30,  # 10-100 (%)
        
        # Axis settings
        'axis_color': '#CCCCCC',
        'background_color': '#1E1E1E',
        
        # Font settings
        'font_size': 10,  # 8-16 pt
        
        # Anti-aliasing
        'antialiasing': True,
        
        # 3D settings
        'scatter_3d_size': 3,  # 1-8 px
        'trajectory_3d_width': 2,  # 1-5 px
    }
    
    def __init__(self):
        """Initialize with default settings"""
        self.settings = self.DEFAULTS.copy()
        self.config_file = Path.home() / '.tsa_plot_settings.json'
        self.load()
    
    def get(self, key: str):
        """Get a setting value"""
        return self.settings.get(key, self.DEFAULTS.get(key))
    
    def set(self, key: str, value):
        """Set a setting value"""
        if key in self.DEFAULTS:
            self.settings[key] = value
    
    def get_color(self, key: str) -> QColor:
        """Get a color setting as QColor"""
        color_str = self.get(key)
        return QColor(color_str)
    
    def set_color(self, key: str, color: QColor):
        """Set a color setting from QColor"""
        self.settings[key] = color.name()
    
    def get_grid_alpha_normalized(self) -> float:
        """Get grid alpha as normalized value (0.0-1.0)"""
        return self.get('grid_alpha') / 100.0
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = self.DEFAULTS.copy()
    
    def save(self):
        """Save settings to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass  # Silent fail
    
    def load(self):
        """Load settings from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    # Only update keys that exist in defaults
                    for key in self.DEFAULTS:
                        if key in loaded:
                            self.settings[key] = loaded[key]
        except Exception:
            self.settings = self.DEFAULTS.copy()
