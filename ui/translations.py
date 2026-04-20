"""
Translation manager for multi-language support
Supports: Turkish (TR) and English (EN)
"""
from typing import Dict


class Translations:
    """Translation database"""
    
    # Translation dictionary
    TEXTS = {
        # Menu Bar
        'menu_file': {'tr': 'Dosya', 'en': 'File'},
        'menu_file_new': {'tr': 'Yeni', 'en': 'New'},
        'menu_file_open': {'tr': 'Aç...', 'en': 'Open...'},
        'menu_file_save': {'tr': 'Kaydet', 'en': 'Save'},
        'menu_file_save_as': {'tr': 'Farklı Kaydet...', 'en': 'Save As...'},
        'menu_file_export': {'tr': 'Dışa Aktar', 'en': 'Export'},
        'menu_file_exit': {'tr': 'Çıkış', 'en': 'Exit'},
        
        # Settings Menu
        'menu_settings': {'tr': 'Ayarlar', 'en': 'Settings'},
        'menu_settings_preferences': {'tr': 'Tercihler', 'en': 'Preferences'},
        'menu_settings_theme': {'tr': 'Tema', 'en': 'Theme'},
        'menu_settings_language': {'tr': 'Dil', 'en': 'Language'},
        
        # Help Menu
        'menu_help': {'tr': 'Yardım', 'en': 'Help'},
        'menu_help_about': {'tr': 'Hakkında', 'en': 'About'},
        'menu_help_documentation': {'tr': 'Belgelendirme', 'en': 'Documentation'},
        
        # Themes
        'theme_dark': {'tr': 'Koyu Tema', 'en': 'Dark Theme'},
        'theme_high_contrast': {'tr': 'Yüksek Kontrast', 'en': 'High Contrast'},
        'theme_scientific': {'tr': 'Bilimsel Tema', 'en': 'Scientific Theme'},
        
        # Languages
        'lang_turkish': {'tr': 'Türkçe', 'en': 'Turkish'},
        'lang_english': {'tr': 'İngilizce', 'en': 'English'},
        
        # Main Window
        'window_title': {'tr': 'Nonlinear Zaman Serisi Analizi', 'en': 'Nonlinear Time Series Analysis'},
        
        # Left Panel - Steps
        'panel_steps': {'tr': 'Analiz Adımları', 'en': 'Analysis Steps'},
        'step_data_load': {'tr': '1. Veri Yükleme', 'en': '1. Data Loading'},
        'step_preprocessing': {'tr': '2. Ön İşleme', 'en': '2. Preprocessing'},
        'step_linear_analysis': {'tr': '3. Lineer Analiz', 'en': '3. Linear Analysis'},
        'step_parameter_estimation': {'tr': '4. Parametre Tahmini', 'en': '4. Parameter Estimation'},
        'step_embedding': {'tr': '5. Gömme (Embedding)', 'en': '5. Embedding'},
        'step_chaos_analysis': {'tr': '6. Kaos Analizi', 'en': '6. Chaos Analysis'},
        'step_results': {'tr': '7. Sonuçlar', 'en': '7. Results'},
        
        # Status indicators
        'status_locked': {'tr': 'Kilitli', 'en': 'Locked'},
        'status_unlocked': {'tr': 'Açık', 'en': 'Unlocked'},
        'status_completed': {'tr': 'Tamamlandı', 'en': 'Completed'},
        'status_in_progress': {'tr': 'İşleniyor', 'en': 'In Progress'},
        
        # Data Loading
        'data_source': {'tr': 'Veri Kaynağı', 'en': 'Data Source'},
        'data_load_file': {'tr': 'Dosyadan Yükle', 'en': 'Load from File'},
        'data_generate': {'tr': 'Sistem Oluştur', 'en': 'Generate System'},
        'data_file_path': {'tr': 'Dosya Yolu', 'en': 'File Path'},
        'data_browse': {'tr': 'Gözat...', 'en': 'Browse...'},
        'data_system_type': {'tr': 'Sistem Tipi', 'en': 'System Type'},
        'data_lorenz': {'tr': 'Lorenz Sistemi', 'en': 'Lorenz System'},
        'data_rossler': {'tr': 'Rössler Sistemi', 'en': 'Rössler System'},
        'data_logistic': {'tr': 'Lojistik Map', 'en': 'Logistic Map'},
        'data_sine': {'tr': 'Sinüs Dalgası', 'en': 'Sine Wave'},
        'data_noise': {'tr': 'Beyaz Gürültü', 'en': 'White Noise'},
        'data_load_button': {'tr': 'Veri Yükle', 'en': 'Load Data'},
        'data_points': {'tr': 'Veri Noktası Sayısı', 'en': 'Number of Data Points'},
        'data_dt': {'tr': 'Zaman Adımı (dt)', 'en': 'Time Step (dt)'},
        
        # Parameters
        'param_tau': {'tr': 'Zaman Gecikmesi (τ)', 'en': 'Time Delay (τ)'},
        'param_m': {'tr': 'Gömme Boyutu (m)', 'en': 'Embedding Dimension (m)'},
        'param_auto': {'tr': 'Otomatik', 'en': 'Auto'},
        'param_manual': {'tr': 'Manuel', 'en': 'Manual'},
        
        # Buttons
        'btn_calculate': {'tr': 'Hesapla', 'en': 'Calculate'},
        'btn_reset': {'tr': 'Sıfırla', 'en': 'Reset'},
        'btn_next': {'tr': 'İleri', 'en': 'Next'},
        'btn_previous': {'tr': 'Geri', 'en': 'Previous'},
        'btn_apply': {'tr': 'Uygula', 'en': 'Apply'},
        'btn_cancel': {'tr': 'İptal', 'en': 'Cancel'},
        'btn_close': {'tr': 'Kapat', 'en': 'Close'},
        
        # Analysis Types
        'analysis_acf': {'tr': 'Otokorelasyon (ACF)', 'en': 'Autocorrelation (ACF)'},
        'analysis_pacf': {'tr': 'Kısmi Otokorelasyon (PACF)', 'en': 'Partial Autocorrelation (PACF)'},
        'analysis_fft': {'tr': 'Fourier Dönüşümü (FFT)', 'en': 'Fourier Transform (FFT)'},
        'analysis_ami': {'tr': 'Ortalama Karşılıklı Bilgi (AMI)', 'en': 'Average Mutual Information (AMI)'},
        'analysis_fnn': {'tr': 'Yalancı En Yakın Komşular (FNN)', 'en': 'False Nearest Neighbors (FNN)'},
        'analysis_lyapunov': {'tr': 'Lyapunov Üssü', 'en': 'Lyapunov Exponent'},
        'analysis_correlation_dim': {'tr': 'Korelasyon Boyutu', 'en': 'Correlation Dimension'},
        
        # Results
        'result_tau_estimated': {'tr': 'Tahmini τ', 'en': 'Estimated τ'},
        'result_m_estimated': {'tr': 'Tahmini m', 'en': 'Estimated m'},
        'result_lyapunov': {'tr': 'Lyapunov Üssü', 'en': 'Lyapunov Exponent'},
        'result_dimension': {'tr': 'Korelasyon Boyutu', 'en': 'Correlation Dimension'},
        
        # Messages
        'msg_data_loaded': {'tr': 'Veri başarıyla yüklendi', 'en': 'Data loaded successfully'},
        'msg_calculating': {'tr': 'Hesaplanıyor...', 'en': 'Calculating...'},
        'msg_completed': {'tr': 'Tamamlandı', 'en': 'Completed'},
        'msg_error': {'tr': 'Hata', 'en': 'Error'},
        'msg_warning': {'tr': 'Uyarı', 'en': 'Warning'},
        'msg_info': {'tr': 'Bilgi', 'en': 'Info'},
        
        # Export
        'export_csv': {'tr': 'CSV Olarak Dışa Aktar', 'en': 'Export as CSV'},
        'export_png': {'tr': 'PNG Olarak Dışa Aktar', 'en': 'Export as PNG'},
        'export_json': {'tr': 'JSON Olarak Dışa Aktar', 'en': 'Export as JSON'},
        
        # About
        'about_title': {'tr': 'Hakkında', 'en': 'About'},
        'about_text': {
            'tr': 'Nonlinear Zaman Serisi Analizi\nVersiyon 1.0\n\nKaotik sistemler için doğrulanabilir analiz aracı.',
            'en': 'Nonlinear Time Series Analysis\nVersion 1.0\n\nVerifiable analysis tool for chaotic systems.'
        },
        
        # Preferences Dialog
        'pref_title': {'tr': 'Tercihler', 'en': 'Preferences'},
        'pref_appearance': {'tr': 'Görünüm', 'en': 'Appearance'},
        'pref_theme': {'tr': 'Tema', 'en': 'Theme'},
        'pref_language': {'tr': 'Dil', 'en': 'Language'},
        'pref_analysis': {'tr': 'Analiz Ayarları', 'en': 'Analysis Settings'},
        'pref_save': {'tr': 'Kaydet', 'en': 'Save'},
        'pref_restore_defaults': {'tr': 'Varsayılanlara Dön', 'en': 'Restore Defaults'},

        # Preprocessing
        'preprocess_operation': {'tr': 'Ön İşlem', 'en': 'Operation'},
        'preprocess_select': {'tr': 'İşlem Seç', 'en': 'Select Operation'},
        'preprocess_params': {'tr': 'Parametreler', 'en': 'Parameters'},
        'preprocess_method': {'tr': 'Yöntem', 'en': 'Method'},
        'preprocess_normalize': {'tr': 'Normalizasyon', 'en': 'Normalize'},
        'preprocess_detrend': {'tr': 'Trend Çıkarma', 'en': 'Detrend'},
        'preprocess_interpolate': {'tr': 'Eksik Veri Doldurma', 'en': 'Interpolate Missing'},
        'preprocess_outlier': {'tr': 'Aykırı Değer Temizleme', 'en': 'Outlier Removal'},
        'preprocess_smooth': {'tr': 'Yumuşatma', 'en': 'Smoothing'},
        'preprocess_difference': {'tr': 'Fark Alma', 'en': 'Differencing'},
        'preprocess_resample': {'tr': 'Yeniden Örnekleme', 'en': 'Resampling'},
        'preprocess_filter': {'tr': 'Filtreleme', 'en': 'Filtering'},
        'preprocess_log': {'tr': 'Log Dönüşümü', 'en': 'Log Transform'},
        'preprocess_boxcox': {'tr': 'Box-Cox Dönüşümü', 'en': 'Box-Cox Transform'},
        'preprocess_window': {'tr': 'Pencere (Crop)', 'en': 'Window (Crop)'},
        'preprocess_denoise': {'tr': 'Gürültü Ayıklama', 'en': 'Denoising'},
        'preprocess_linear': {'tr': 'Doğrusal', 'en': 'Linear'},
        'preprocess_polynomial': {'tr': 'Polinom', 'en': 'Polynomial'},
        'preprocess_mean_removal': {'tr': 'Ortalama Çıkarma', 'en': 'Mean Removal'},
        'preprocess_nearest': {'tr': 'En Yakın', 'en': 'Nearest'},
        'preprocess_poly_order': {'tr': 'Polinom Derecesi', 'en': 'Polynomial Order'},
        'preprocess_threshold': {'tr': 'Eşik Değeri', 'en': 'Threshold'},
        'preprocess_moving_avg': {'tr': 'Hareketli Ortalama', 'en': 'Moving Average'},
        'preprocess_window_size': {'tr': 'Pencere Boyutu', 'en': 'Window Size'},
        'preprocess_diff_order': {'tr': 'Fark Derecesi', 'en': 'Difference Order'},
        'preprocess_resample_factor': {'tr': 'Örnekleme Faktörü', 'en': 'Resample Factor'},
        'preprocess_filter_type': {'tr': 'Filtre Tipi', 'en': 'Filter Type'},
        'preprocess_lowpass': {'tr': 'Alçak Geçiren', 'en': 'Lowpass'},
        'preprocess_highpass': {'tr': 'Yüksek Geçiren', 'en': 'Highpass'},
        'preprocess_bandpass': {'tr': 'Bant Geçiren', 'en': 'Bandpass'},
        'preprocess_cutoff': {'tr': 'Kesim Frekansı', 'en': 'Cutoff Frequency'},
        'preprocess_highcut': {'tr': 'Üst Kesim Frekansı', 'en': 'High Cutoff'},
        'preprocess_filter_order': {'tr': 'Filtre Derecesi', 'en': 'Filter Order'},
        'preprocess_log_info': {'tr': 'Logaritmik dönüşüm uygular.\nNegatif değerler otomatik kaydırılır.', 'en': 'Applies log transform.\nNegative values are automatically shifted.'},
        'preprocess_boxcox_info': {'tr': 'Box-Cox dönüşümü uygular.\nOptimal λ otomatik bulunur.', 'en': 'Applies Box-Cox transform.\nOptimal λ is found automatically.'},
        'preprocess_start_idx': {'tr': 'Başlangıç İndeksi', 'en': 'Start Index'},
        'preprocess_end_idx': {'tr': 'Bitiş İndeksi', 'en': 'End Index'},
        'preprocess_wavelet': {'tr': 'Dalgacık (Wavelet)', 'en': 'Wavelet'},
        'preprocess_median_filter': {'tr': 'Medyan Filtre', 'en': 'Median Filter'},
        'preprocess_decomp_level': {'tr': 'Dekompozisyon Seviyesi', 'en': 'Decomposition Level'},
        'preprocess_points': {'tr': 'nokta', 'en': 'points'},
        'preprocess_reset_done': {'tr': 'Orijinal veriye geri dönüldü.', 'en': 'Reset to original data.'},
    }


class TranslationManager:
    """Manage application translations"""
    
    def __init__(self, default_language: str = 'tr'):
        self.current_language = default_language
        self.available_languages = ['tr', 'en']
    
    def get_text(self, key: str) -> str:
        """Get translated text for key"""
        if key in Translations.TEXTS:
            return Translations.TEXTS[key].get(self.current_language, key)
        return key
    
    def set_language(self, language: str):
        """Set current language"""
        if language in self.available_languages:
            self.current_language = language
    
    def get_current_language(self) -> str:
        """Get current language code"""
        return self.current_language
    
    def get_available_languages(self) -> list:
        """Get list of available language codes"""
        return self.available_languages
    
    def __call__(self, key: str) -> str:
        """Shorthand for get_text"""
        return self.get_text(key)
