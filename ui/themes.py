"""
Theme manager for UI
Supports: Dark Mode (default), High Contrast, Scientific (Solarized)
"""
from typing import Dict


class Theme:
    """Base theme class"""
    
    def __init__(self):
        self.name = "Base"
        self.colors = {}
        self.stylesheet = ""
    
    def get_stylesheet(self) -> str:
        """Return Qt stylesheet"""
        return self.stylesheet


class DarkTheme(Theme):
    """Dark mode theme (DEFAULT)"""
    
    def __init__(self):
        super().__init__()
        self.name = "Dark"
        
        self.colors = {
            'background': '#1e1e1e',
            'background_secondary': '#252525',
            'background_tertiary': '#2d2d2d',
            'foreground': '#d4d4d4',
            'foreground_secondary': '#9d9d9d',
            'accent': '#0e639c',
            'accent_hover': '#1177bb',
            'border': '#3f3f3f',
            'selection': '#264f78',
            'error': '#f48771',
            'warning': '#cca700',
            'success': '#89d185',
            'plot_bg': '#1e1e1e',
            'plot_grid': '#3f3f3f',
            'plot_text': '#d4d4d4'
        }
        
        self.stylesheet = f"""
            QMainWindow {{
                background-color: {self.colors['background']};
                color: {self.colors['foreground']};
            }}
            
            QWidget {{
                background-color: {self.colors['background']};
                color: {self.colors['foreground']};
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 10pt;
            }}
            
            QMenuBar {{
                background-color: {self.colors['background_secondary']};
                color: {self.colors['foreground']};
                border-bottom: 1px solid {self.colors['border']};
                padding: 2px;
            }}
            
            QMenuBar::item {{
                background-color: transparent;
                padding: 4px 12px;
            }}
            
            QMenuBar::item:selected {{
                background-color: {self.colors['accent']};
            }}
            
            QMenu {{
                background-color: {self.colors['background_secondary']};
                color: {self.colors['foreground']};
                border: 1px solid {self.colors['border']};
            }}
            
            QMenu::item {{
                padding: 6px 24px;
            }}
            
            QMenu::item:selected {{
                background-color: {self.colors['accent']};
            }}
            
            QPushButton {{
                background-color: {self.colors['background_tertiary']};
                color: {self.colors['foreground']};
                border: 1px solid {self.colors['border']};
                padding: 6px 16px;
                border-radius: 3px;
            }}
            
            QPushButton:hover {{
                background-color: {self.colors['accent']};
                border-color: {self.colors['accent_hover']};
            }}
            
            QPushButton:pressed {{
                background-color: {self.colors['accent_hover']};
            }}
            
            QPushButton:disabled {{
                background-color: {self.colors['background_secondary']};
                color: {self.colors['foreground_secondary']};
            }}
            
            QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {{
                background-color: {self.colors['background_tertiary']};
                color: {self.colors['foreground']};
                border: 1px solid {self.colors['border']};
                padding: 4px;
                border-radius: 2px;
            }}
            
            QSpinBox, QDoubleSpinBox {{
                background-color: {self.colors['background_tertiary']};
                color: {self.colors['foreground']};
                border: 1px solid {self.colors['border']};
                padding: 4px;
                padding-right: 25px;
                border-radius: 2px;
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border: 1px solid {self.colors['accent']};
            }}
            
            QLabel {{
                background-color: transparent;
                color: {self.colors['foreground']};
            }}
            
            QGroupBox {{
                background-color: {self.colors['background_secondary']};
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                font-weight: bold;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 4px;
                color: {self.colors['foreground']};
            }}
            
            QListWidget, QTreeWidget {{
                background-color: {self.colors['background_tertiary']};
                color: {self.colors['foreground']};
                border: 1px solid {self.colors['border']};
                outline: none;
            }}
            
            QListWidget::item:selected, QTreeWidget::item:selected {{
                background-color: {self.colors['selection']};
            }}
            
            QListWidget::item:hover, QTreeWidget::item:hover {{
                background-color: {self.colors['background_secondary']};
            }}
            
            QScrollBar:vertical {{
                background-color: {self.colors['background']};
                width: 14px;
                border: none;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {self.colors['border']};
                min-height: 20px;
                border-radius: 7px;
                margin: 2px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {self.colors['foreground_secondary']};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background-color: {self.colors['background']};
                height: 14px;
                border: none;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {self.colors['border']};
                min-width: 20px;
                border-radius: 7px;
                margin: 2px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {self.colors['foreground_secondary']};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            
            QTabWidget::pane {{
                border: 1px solid {self.colors['border']};
                background-color: {self.colors['background']};
            }}
            
            QTabBar::tab {{
                background-color: {self.colors['background_secondary']};
                color: {self.colors['foreground']};
                padding: 8px 16px;
                border: 1px solid {self.colors['border']};
                border-bottom: none;
            }}
            
            QTabBar::tab:selected {{
                background-color: {self.colors['background']};
                border-bottom: 2px solid {self.colors['accent']};
            }}
            
            QTabBar::tab:hover {{
                background-color: {self.colors['background_tertiary']};
            }}
            
            QStatusBar {{
                background-color: {self.colors['background_secondary']};
                color: {self.colors['foreground']};
                border-top: 1px solid {self.colors['border']};
            }}
        """


class HighContrastTheme(Theme):
    """High contrast theme for accessibility"""
    
    def __init__(self):
        super().__init__()
        self.name = "High Contrast"
        
        self.colors = {
            'background': '#000000',
            'background_secondary': '#1a1a1a',
            'background_tertiary': '#2a2a2a',
            'foreground': '#ffffff',
            'foreground_secondary': '#cccccc',
            'accent': '#00ff00',
            'accent_hover': '#00cc00',
            'border': '#ffffff',
            'selection': '#0000ff',
            'error': '#ff0000',
            'warning': '#ffff00',
            'success': '#00ff00',
            'plot_bg': '#000000',
            'plot_grid': '#ffffff',
            'plot_text': '#ffffff'
        }
        
        self.stylesheet = f"""
            QMainWindow, QWidget {{
                background-color: {self.colors['background']};
                color: {self.colors['foreground']};
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 11pt;
                font-weight: bold;
            }}
            
            QMenuBar {{
                background-color: {self.colors['background']};
                color: {self.colors['foreground']};
                border-bottom: 2px solid {self.colors['border']};
            }}
            
            QMenuBar::item:selected {{
                background-color: {self.colors['accent']};
                color: {self.colors['background']};
            }}
            
            QMenu {{
                background-color: {self.colors['background']};
                color: {self.colors['foreground']};
                border: 2px solid {self.colors['border']};
            }}
            
            QMenu::item:selected {{
                background-color: {self.colors['accent']};
                color: {self.colors['background']};
            }}
            
            QPushButton {{
                background-color: {self.colors['background_secondary']};
                color: {self.colors['foreground']};
                border: 2px solid {self.colors['border']};
                padding: 8px 20px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {self.colors['accent']};
                color: {self.colors['background']};
            }}
            
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {self.colors['background_secondary']};
                color: {self.colors['foreground']};
                border: 2px solid {self.colors['border']};
                padding: 6px;
            }}
            
            QLineEdit:focus, QTextEdit:focus {{
                border: 2px solid {self.colors['accent']};
            }}
            
            QGroupBox {{
                background-color: {self.colors['background']};
                border: 2px solid {self.colors['border']};
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }}
            
            QListWidget, QTreeWidget {{
                background-color: {self.colors['background_secondary']};
                color: {self.colors['foreground']};
                border: 2px solid {self.colors['border']};
            }}
            
            QListWidget::item:selected, QTreeWidget::item:selected {{
                background-color: {self.colors['selection']};
                color: {self.colors['foreground']};
            }}
            
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
                background-color: {self.colors['foreground']};
                border: 2px solid {self.colors['border']};
            }}
        """


class ScientificTheme(Theme):
    """Scientific theme based on teal-green palette (#31585c)"""
    
    def __init__(self):
        super().__init__()
        self.name = "Scientific"
        
        # Teal-green palette around #31585c
        self.colors = {
            'background': '#1a2e30',        # Darker base
            'background_secondary': '#213a3d',  # Slightly lighter
            'background_tertiary': '#2a4649',   # Medium
            'foreground': '#d4e4e5',        # Light text
            'foreground_secondary': '#9db9bb',  # Muted text
            'accent': '#31585c',            # Main color
            'accent_hover': '#3d6e73',      # Lighter hover
            'border': '#2a4649',
            'selection': '#31585c',
            'error': '#d9534f',             # Red
            'warning': '#f0ad4e',           # Orange
            'success': '#5cb85c',           # Green
            'plot_bg': '#1a2e30',
            'plot_grid': '#2a4649',
            'plot_text': '#d4e4e5',
            'violet': '#7e8aa2',
            'magenta': '#b66d8f'
        }
        
        self.stylesheet = f"""
            QMainWindow, QWidget {{
                background-color: {self.colors['background']};
                color: {self.colors['foreground']};
                font-family: "Consolas", "Courier New", monospace;
                font-size: 10pt;
            }}
            
            QMenuBar {{
                background-color: {self.colors['background_secondary']};
                color: {self.colors['foreground']};
                border-bottom: 1px solid {self.colors['border']};
            }}
            
            QMenuBar::item:selected {{
                background-color: {self.colors['accent']};
                color: {self.colors['background']};
            }}
            
            QMenu {{
                background-color: {self.colors['background_secondary']};
                color: {self.colors['foreground']};
                border: 1px solid {self.colors['accent']};
            }}
            
            QMenu::item:selected {{
                background-color: {self.colors['accent']};
                color: {self.colors['background']};
            }}
            
            QPushButton {{
                background-color: {self.colors['background_secondary']};
                color: {self.colors['foreground']};
                border: 1px solid {self.colors['accent']};
                padding: 6px 16px;
                border-radius: 2px;
            }}
            
            QPushButton:hover {{
                background-color: {self.colors['accent']};
                color: {self.colors['background']};
            }}
            
            QPushButton:pressed {{
                background-color: {self.colors['accent_hover']};
            }}
            
            QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background-color: {self.colors['background_secondary']};
                color: {self.colors['foreground']};
                border: 1px solid {self.colors['border']};
                padding: 4px;
                selection-background-color: {self.colors['selection']};
            }}
            
            QLineEdit:focus, QTextEdit:focus {{
                border: 1px solid {self.colors['accent']};
            }}
            
            QLabel {{
                background-color: transparent;
                color: {self.colors['foreground']};
            }}
            
            QGroupBox {{
                background-color: {self.colors['background']};
                border: 1px solid {self.colors['accent']};
                border-radius: 3px;
                margin-top: 8px;
                padding-top: 8px;
                color: {self.colors['accent']};
                font-weight: bold;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 4px;
            }}
            
            QListWidget, QTreeWidget {{
                background-color: {self.colors['background_secondary']};
                color: {self.colors['foreground']};
                border: 1px solid {self.colors['border']};
                alternate-background-color: {self.colors['background']};
            }}
            
            QListWidget::item:selected, QTreeWidget::item:selected {{
                background-color: {self.colors['selection']};
                color: {self.colors['foreground']};
            }}
            
            QScrollBar:vertical {{
                background-color: {self.colors['background']};
                width: 12px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {self.colors['accent']};
                min-height: 20px;
            }}
            
            QScrollBar:horizontal {{
                background-color: {self.colors['background']};
                height: 12px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {self.colors['accent']};
                min-width: 20px;
            }}
            
            QTabWidget::pane {{
                border: 1px solid {self.colors['border']};
            }}
            
            QTabBar::tab {{
                background-color: {self.colors['background_secondary']};
                color: {self.colors['foreground']};
                padding: 8px 16px;
                border: 1px solid {self.colors['border']};
            }}
            
            QTabBar::tab:selected {{
                background-color: {self.colors['background']};
                color: {self.colors['accent']};
                border-bottom: 2px solid {self.colors['accent']};
            }}
            
            QStatusBar {{
                background-color: {self.colors['background_secondary']};
                color: {self.colors['foreground']};
                border-top: 1px solid {self.colors['border']};
            }}
        """


class ThemeManager:
    """Manage application themes"""
    
    def __init__(self):
        self.themes: Dict[str, Theme] = {
            'dark': DarkTheme(),
            'high_contrast': HighContrastTheme(),
            'scientific': ScientificTheme()
        }
        self.current_theme = 'dark'  # Default
    
    def get_theme(self, theme_name: str = None) -> Theme:
        """Get theme by name"""
        if theme_name is None:
            theme_name = self.current_theme
        return self.themes.get(theme_name, self.themes['dark'])
    
    def set_theme(self, theme_name: str):
        """Set current theme"""
        if theme_name in self.themes:
            self.current_theme = theme_name
    
    def get_available_themes(self) -> list:
        """Get list of available theme names"""
        return list(self.themes.keys())
