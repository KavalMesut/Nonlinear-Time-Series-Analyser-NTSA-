"""
Main window for Nonlinear Time Series Analyzer
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QMenuBar, QMenu, QStatusBar, QSplitter, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from pathlib import Path

from .themes import ThemeManager
from .translations import TranslationManager
from .plot_settings import PlotSettings
from .panels.steps_panel import StepsPanel
from .panels.content_panel import ContentPanel
from .panels.plot_panel import PlotPanel
from .dialogs.preferences_dialog import PreferencesDialog
from core.session import AnalysisSession
from core.export import export_timeseries_csv, export_plot_png, export_analysis_results_json


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
        self.plot_settings = PlotSettings()
        
        # Session
        self.current_session = AnalysisSession()
        self.current_file_path = None  # Son kaydedilen .tsa dosya yolu
        
        # Initialize UI
        self.init_ui()
        
        # Apply default theme (dark mode)
        self.apply_theme('dark')
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle(self.tr('window_title'))
        self.setGeometry(100, 100, 1400, 900)
        
        # Maximize window on startup
        self.showMaximized()
        
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
        self.plot_panel = PlotPanel(self.theme_manager, self.plot_settings)
        splitter.addWidget(self.plot_panel)
        
        # ContentPanel'den gelen grafik isteklerini PlotPanel'e bagla
        self.content_panel.plot_requested.connect(self.plot_panel.handle_plot)
        
        # Splitter oranlari (%20 sol, %30 orta, %50 sag)
        splitter.setSizes([280, 420, 700])
        
        # Splitter handle stilini ayarla (gorunur yap)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #555555;
                border: 1px solid #333333;
            }
            QSplitter::handle:hover {
                background-color: #777777;
            }
        """)
        
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
        """Yeni analiz başlat (mevcut session'ı sıfırla)"""
        # Kaydedilmemiş değişiklikler varsa uyar
        reply = QMessageBox.question(
            self,
            self.tr('menu_file_new'),
            "Mevcut analiz sıfırlanacak. Devam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.current_session = AnalysisSession()
            self.current_file_path = None
            self.content_panel.reset_all()
            self.plot_panel.clear_plot()
            self.status_bar.showMessage("Yeni analiz başlatıldı")
    
    def open_file(self):
        """Session dosyası aç (.tsa veya .json)"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Analiz Dosyası Aç",
            str(Path.home()),
            "TSA Files (*.tsa);;JSON Files (*.json);;All Files (*.*)"
        )
        
        if filepath:
            # .tsa → pickle, .json → JSON
            if filepath.endswith('.tsa'):
                session = AnalysisSession.load_pickle(filepath)
            else:
                session = AnalysisSession.load_json(filepath)
            
            if session:
                self.current_session = session
                self.current_file_path = filepath
                self._restore_session(session)
                self.status_bar.showMessage(f"Yüklendi: {Path(filepath).name}")
            else:
                QMessageBox.warning(self, "Hata", "Dosya yüklenemedi!")
    
    def save_analysis(self):
        """Mevcut session'ı kaydet"""
        if self.current_file_path:
            # Varolan dosyaya kaydet
            self._save_to_file(self.current_file_path)
        else:
            # İlk kayıt → "Save As" diyaloğu
            self.save_analysis_as()
    
    def save_analysis_as(self):
        """Session'ı yeni dosyaya kaydet"""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Analizi Kaydet",
            str(Path.home() / "analysis.tsa"),
            "TSA Files (*.tsa);;JSON Files (*.json);;All Files (*.*)"
        )
        
        if filepath:
            self._save_to_file(filepath)
    
    def _save_to_file(self, filepath: str):
        """Session'ı dosyaya kaydet (internal)"""
        # Session'ı güncelle
        self._update_session_from_ui()
        
        # Uzantıya göre format seç
        if filepath.endswith('.tsa'):
            success = self.current_session.save_pickle(filepath)
        else:
            success = self.current_session.save_json(filepath)
        
        if success:
            self.current_file_path = filepath
            self.status_bar.showMessage(f"Kaydedildi: {Path(filepath).name}")
        else:
            QMessageBox.warning(self, "Hata", "Dosya kaydedilemedi!")
    
    def _update_session_from_ui(self):
        """UI'dan session'a mevcut durumu aktar"""
        # Timeseries
        if self.content_panel.current_data:
            self.current_session.set_timeseries(self.content_panel.current_data, is_original=False)
        
        # Parameters
        if hasattr(self.content_panel, 'parameter_panel'):
            tau = self.content_panel.parameter_panel.tau
            m = self.content_panel.parameter_panel.m
            if tau and m:
                self.current_session.set_parameters(tau, m)
        
        # Analysis results (her panelden topla)
        # TODO: Her panel kendi sonuçlarını session'a yazsın
    
    def _restore_session(self, session: AnalysisSession):
        """Session'dan UI'ya verileri yükle"""
        # Timeseries'i content panel'e yükle
        if session.timeseries:
            self.content_panel.on_data_loaded(session.timeseries)
        
        # Parameters'ı set et
        if session.tau and session.m:
            if hasattr(self.content_panel, 'parameter_panel'):
                self.content_panel.parameter_panel.tau = session.tau
                self.content_panel.parameter_panel.m = session.m
                self.content_panel.parameter_panel.tau_result_label.setText(f"τ = {session.tau}")
                self.content_panel.parameter_panel.m_result_label.setText(f"m = {session.m}")
        
        # TODO: Analysis results'ları restore et
    
    def export_csv(self):
        """Mevcut zaman serisini CSV olarak dışa aktar"""
        if not self.content_panel.current_data:
            QMessageBox.warning(self, "Uyarı", "Dışa aktarılacak veri yok!")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "CSV Olarak Dışa Aktar",
            str(Path.home() / "timeseries.csv"),
            "CSV Files (*.csv);;All Files (*.*)"
        )
        
        if filepath:
            success = export_timeseries_csv(
                self.content_panel.current_data,
                filepath,
                include_metadata=True
            )
            if success:
                self.status_bar.showMessage(f"CSV dışa aktarıldı: {Path(filepath).name}")
            else:
                QMessageBox.warning(self, "Hata", "CSV dışa aktarılamadı!")
    
    def export_png(self):
        """Mevcut grafiği PNG olarak dışa aktar"""
        if not self.plot_panel.plot_widget:
            QMessageBox.warning(self, "Uyarı", "Dışa aktarılacak grafik yok!")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "PNG Olarak Dışa Aktar",
            str(Path.home() / "plot.png"),
            "PNG Files (*.png);;All Files (*.*)"
        )
        
        if filepath:
            success = export_plot_png(
                self.plot_panel.plot_widget,
                filepath,
                width=1920,
                height=1080
            )
            if success:
                self.status_bar.showMessage(f"PNG dışa aktarıldı: {Path(filepath).name}")
            else:
                QMessageBox.warning(self, "Hata", "PNG dışa aktarılamadı!")
    
    def export_json(self):
        """Analiz sonuçlarını JSON olarak dışa aktar"""
        # Session'daki tüm sonuçları JSON'a dök
        self._update_session_from_ui()
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "JSON Olarak Dışa Aktar",
            str(Path.home() / "analysis_results.json"),
            "JSON Files (*.json);;All Files (*.*)"
        )
        
        if filepath:
            success = export_analysis_results_json(
                self.current_session.to_dict(),
                filepath
            )
            if success:
                self.status_bar.showMessage(f"JSON dışa aktarıldı: {Path(filepath).name}")
            else:
                QMessageBox.warning(self, "Hata", "JSON dışa aktarılamadı!")
    
    def show_preferences(self):
        """Show preferences dialog"""
        # Backup current settings in case user cancels
        settings_backup = self.plot_settings.settings.copy()
        
        dialog = PreferencesDialog(
            self,
            self.theme_manager,
            self.translation_manager,
            self.plot_settings
        )
        
        # Connect live update signal
        dialog.plot_settings_changed.connect(self.plot_panel.apply_settings)
        
        if dialog.exec():
            # User clicked Save - apply all changes
            theme = dialog.get_selected_theme()
            language = dialog.get_selected_language()
            
            # Save plot settings to file
            self.plot_settings.save()
            
            if theme != self.theme_manager.current_theme:
                self.apply_theme(theme)
            
            if language != self.translation_manager.current_language:
                self.set_language(language)
        else:
            # User clicked Cancel - restore backup
            self.plot_settings.settings = settings_backup
            self.plot_panel.apply_settings()
    
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
