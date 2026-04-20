"""
Main window for Nonlinear Time Series Analyzer
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QMenuBar, QMenu, QStatusBar, QSplitter, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from .themes import ThemeManager
from .translations import TranslationManager
from .panels.steps_panel import StepsPanel
from .panels.content_panel import ContentPanel
from .panels.plot_panel import PlotPanel
from .dialogs.preferences_dialog import PreferencesDialog


class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signals
    theme_changed = Signal(str)
    language_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        # Managers
        self.theme_manager = ThemeManager()
        self.translation_manager = TranslationManager(default_language='tr')
        
        # Initialize UI
        self.init_ui()
        
        # Apply default theme (dark mode)
        self.apply_theme('dark')
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle(self.tr('window_title'))
        self.setGeometry(100, 100, 1400, 900)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for resizable panels (3 dikey bolme)
        splitter = QSplitter(Qt.Horizontal)
        
        # Sol panel — Analiz Adimlari
        self.steps_panel = StepsPanel(self.translation_manager)
        splitter.addWidget(self.steps_panel)
        
        # Orta panel — Kontroller / Veri
        self.content_panel = ContentPanel(self.translation_manager, self.theme_manager)
        splitter.addWidget(self.content_panel)
        
        # Sag panel — Grafik
        self.plot_panel = PlotPanel(self.theme_manager)
        splitter.addWidget(self.plot_panel)
        
        # ContentPanel'den gelen grafik isteklerini PlotPanel'e bagla
        self.content_panel.plot_requested.connect(self.plot_panel.handle_plot)
        
        # Splitter oranlari (%20 sol, %30 orta, %50 sag)
        splitter.setSizes([280, 420, 700])
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(self.tr('msg_info') + ': ' + 
                                   self.tr('window_title'))
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu(self.tr('menu_file'))
        
        new_action = QAction(self.tr('menu_file_new'), self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_analysis)
        file_menu.addAction(new_action)
        
        open_action = QAction(self.tr('menu_file_open'), self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction(self.tr('menu_file_save'), self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_analysis)
        file_menu.addAction(save_action)
        
        save_as_action = QAction(self.tr('menu_file_save_as'), self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_analysis_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Export submenu
        export_menu = file_menu.addMenu(self.tr('menu_file_export'))
        
        export_csv = QAction(self.tr('export_csv'), self)
        export_csv.triggered.connect(self.export_csv)
        export_menu.addAction(export_csv)
        
        export_png = QAction(self.tr('export_png'), self)
        export_png.triggered.connect(self.export_png)
        export_menu.addAction(export_png)
        
        export_json = QAction(self.tr('export_json'), self)
        export_json.triggered.connect(self.export_json)
        export_menu.addAction(export_json)
        
        file_menu.addSeparator()
        
        exit_action = QAction(self.tr('menu_file_exit'), self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings Menu
        settings_menu = menubar.addMenu(self.tr('menu_settings'))
        
        preferences_action = QAction(self.tr('menu_settings_preferences'), self)
        preferences_action.setShortcut('Ctrl+,')
        preferences_action.triggered.connect(self.show_preferences)
        settings_menu.addAction(preferences_action)
        
        settings_menu.addSeparator()
        
        # Theme submenu
        theme_menu = settings_menu.addMenu(self.tr('menu_settings_theme'))
        
        dark_theme_action = QAction(self.tr('theme_dark'), self)
        dark_theme_action.triggered.connect(lambda: self.apply_theme('dark'))
        theme_menu.addAction(dark_theme_action)
        
        high_contrast_action = QAction(self.tr('theme_high_contrast'), self)
        high_contrast_action.triggered.connect(lambda: self.apply_theme('high_contrast'))
        theme_menu.addAction(high_contrast_action)
        
        scientific_action = QAction(self.tr('theme_scientific'), self)
        scientific_action.triggered.connect(lambda: self.apply_theme('scientific'))
        theme_menu.addAction(scientific_action)
        
        # Language submenu
        language_menu = settings_menu.addMenu(self.tr('menu_settings_language'))
        
        turkish_action = QAction(self.tr('lang_turkish'), self)
        turkish_action.triggered.connect(lambda: self.set_language('tr'))
        language_menu.addAction(turkish_action)
        
        english_action = QAction(self.tr('lang_english'), self)
        english_action.triggered.connect(lambda: self.set_language('en'))
        language_menu.addAction(english_action)
        
        # Help Menu
        help_menu = menubar.addMenu(self.tr('menu_help'))
        
        about_action = QAction(self.tr('menu_help_about'), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        doc_action = QAction(self.tr('menu_help_documentation'), self)
        doc_action.triggered.connect(self.show_documentation)
        help_menu.addAction(doc_action)
    
    def tr(self, key: str) -> str:
        """Translate text"""
        return self.translation_manager.get_text(key)
    
    def apply_theme(self, theme_name: str):
        """Apply theme to application"""
        theme = self.theme_manager.get_theme(theme_name)
        self.setStyleSheet(theme.get_stylesheet())
        self.theme_manager.set_theme(theme_name)
        self.theme_changed.emit(theme_name)
        
        # Update panels with new theme
        if hasattr(self, 'content_panel'):
            self.content_panel.update_plot_theme()
        if hasattr(self, 'plot_panel'):
            self.plot_panel.update_plot_theme()
    
    def set_language(self, language: str):
        """Set application language"""
        self.translation_manager.set_language(language)
        self.language_changed.emit(language)
        
        # Refresh UI with new language
        self.refresh_ui()
    
    def refresh_ui(self):
        """Refresh UI elements with current language"""
        self.setWindowTitle(self.tr('window_title'))
        
        # Recreate menu bar
        self.menuBar().clear()
        self.create_menu_bar()
        
        # Refresh panels
        if hasattr(self, 'steps_panel'):
            self.steps_panel.refresh_ui()
        if hasattr(self, 'content_panel'):
            self.content_panel.refresh_ui()
        
        self.status_bar.showMessage(self.tr('msg_info') + ': ' + 
                                   self.tr('window_title'))
    
    # Menu actions
    def new_analysis(self):
        """Start new analysis"""
        # TODO: Implement
        self.status_bar.showMessage(self.tr('menu_file_new'))
    
    def open_file(self):
        """Open file"""
        # TODO: Implement
        self.status_bar.showMessage(self.tr('menu_file_open'))
    
    def save_analysis(self):
        """Save analysis"""
        # TODO: Implement
        self.status_bar.showMessage(self.tr('menu_file_save'))
    
    def save_analysis_as(self):
        """Save analysis as"""
        # TODO: Implement
        self.status_bar.showMessage(self.tr('menu_file_save_as'))
    
    def export_csv(self):
        """Export as CSV"""
        # TODO: Implement
        self.status_bar.showMessage(self.tr('export_csv'))
    
    def export_png(self):
        """Export as PNG"""
        # TODO: Implement
        self.status_bar.showMessage(self.tr('export_png'))
    
    def export_json(self):
        """Export as JSON"""
        # TODO: Implement
        self.status_bar.showMessage(self.tr('export_json'))
    
    def show_preferences(self):
        """Show preferences dialog"""
        dialog = PreferencesDialog(
            self,
            self.theme_manager,
            self.translation_manager
        )
        if dialog.exec():
            # Apply changes
            theme = dialog.get_selected_theme()
            language = dialog.get_selected_language()
            
            if theme != self.theme_manager.current_theme:
                self.apply_theme(theme)
            
            if language != self.translation_manager.current_language:
                self.set_language(language)
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            self.tr('about_title'),
            self.tr('about_text')
        )
    
    def show_documentation(self):
        """Show documentation"""
        # TODO: Implement
        self.status_bar.showMessage(self.tr('menu_help_documentation'))
