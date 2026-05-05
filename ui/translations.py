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
        'step_phase_space': {'tr': '5. Faz Uzayı', 'en': '5. Phase Space'},
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
        # Custom system
        'data_ode':            {'tr': 'ODE',              'en': 'ODE'},
        'data_discrete_map':   {'tr': 'Kesikli Harita',   'en': 'Discrete Map'},
        'data_test_systems':   {'tr': 'Test Sistemleri',  'en': 'Test Systems'},
        'data_eq_count':       {'tr': 'Denklem Sayısı',   'en': 'Equation Count'},
        'data_output_var':     {'tr': 'Çıktı Değişkeni',  'en': 'Output Variable'},
        'data_parameters':     {'tr': 'Parametreler',      'en': 'Parameters'},
        'data_n_points':       {'tr': 'Nokta Sayısı',      'en': 'Number of Points'},
        'data_timestep':       {'tr': 'Zaman Adımı (dt)', 'en': 'Time Step (dt)'},
        'data_drag_drop':      {'tr': 'Sürükle-Bırak',     'en': 'Drag & Drop'},

        # Data table
        'table_summary':       {'tr': 'Veri Özeti',       'en': 'Data Summary'},
        'table_length':        {'tr': 'Uzunluk',           'en': 'Length'},
        'table_duration':      {'tr': 'Toplam Süre',       'en': 'Total Duration'},
        'table_system':        {'tr': 'Sistem',            'en': 'System'},
        'table_params':        {'tr': 'Parametreler',      'en': 'Parameters'},
        'table_stats':         {'tr': 'İstatistik',        'en': 'Statistics'},
        'table_index':         {'tr': 'İndeks',            'en': 'Index'},
        'table_time':          {'tr': 'Zaman',             'en': 'Time'},
        'table_value':         {'tr': 'Değer',             'en': 'Value'},
        'table_mean':          {'tr': 'Ort',               'en': 'Mean'},
        'table_std':           {'tr': 'Std',               'en': 'Std'},
        'msg_unknown':         {'tr': 'Bilinmiyor',        'en': 'Unknown'},

        # Plot panel
        'plot_title':              {'tr': 'Grafik',                        'en': 'Plot'},
        'plot_compare_label':      {'tr': 'Karşılaştırma Grafiği:',        'en': 'Comparison Plot:'},
        'plot_empty':              {'tr': '(Boş)',                         'en': '(Empty)'},
        'plot_clear':              {'tr': 'Temizle',                       'en': 'Clear'},
        'plot_time_series':        {'tr': 'Zaman Serisi',                  'en': 'Time Series'},
        'plot_linear':             {'tr': 'Lineer',                        'en': 'Linear'},
        'plot_preprocessing':      {'tr': 'Ön İşleme',                     'en': 'Preprocessing'},
        'plot_lyapunov_spectrum':  {'tr': 'Lyapunov Spektrumu',            'en': 'Lyapunov Spectrum'},
        'plot_correlation_dim':    {'tr': 'Korelasyon Boyutu',             'en': 'Correlation Dimension'},
        'plot_fft_power':          {'tr': 'FFT Güç Spektrumu',             'en': 'FFT Power Spectrum'},
        'plot_ami_delay':          {'tr': 'AMI - Zaman Gecikmesi Tahmini', 'en': 'AMI - Time Delay Estimation'},
        'plot_fnn_dim':            {'tr': 'FNN - Gömme Boyutu Tahmini',    'en': 'FNN - Embedding Dimension Estimation'},
        'plot_lyapunov':           {'tr': 'Lyapunov',                      'en': 'Lyapunov'},
        'plot_time':               {'tr': 'Zaman',                         'en': 'Time'},
        'plot_value':              {'tr': 'Değer',                         'en': 'Value'},
        'plot_lag':                {'tr': 'Gecikme',                       'en': 'Lag'},
        'plot_frequency':          {'tr': 'Frekans (Hz)',                  'en': 'Frequency (Hz)'},
        'plot_power':              {'tr': 'Güç',                           'en': 'Power'},
        'plot_dimension':          {'tr': 'Boyut',                         'en': 'Dimension'},
        'plot_exponent_index':     {'tr': 'Üs İndeksi',                    'en': 'Exponent Index'},
        'plot_original':           {'tr': 'Orijinal',                      'en': 'Original'},
        'plot_processed':          {'tr': 'İşlenmiş',                      'en': 'Processed'},
        'plot_start':              {'tr': 'Başlangıç',                     'en': 'Start'},
        'plot_end':                {'tr': 'Bitiş',                         'en': 'End'},
        'plot_diagonal':           {'tr': 'y=x',                           'en': 'y=x'},

        # Chaos analysis panel
        'chaos_params':           {'tr': 'Parametreler',               'en': 'Parameters'},
        'chaos_manual_params':    {'tr': 'Manuel Parametreleri Kullan','en': 'Use Manual Parameters'},
        'chaos_wolf':             {'tr': 'Wolf Algoritması',            'en': 'Wolf Algorithm'},
        'chaos_rosenstein':       {'tr': 'Rosenstein Algoritması',      'en': 'Rosenstein Algorithm'},
        'chaos_kantz':            {'tr': 'Kantz Algoritması',           'en': 'Kantz Algorithm'},
        'chaos_benettin':         {'tr': 'Benettin (ODE - altın standart)', 'en': 'Benettin (ODE - gold standard)'},
        'chaos_spectrum_group':   {'tr': 'Lyapunov Spektrumu',          'en': 'Lyapunov Spectrum'},
        'chaos_calc_spectrum':    {'tr': 'Tam Spektrumu Hesapla',       'en': 'Calculate Full Spectrum'},
        'chaos_calc_corr':        {'tr': 'Korelasyon Boyutu Hesapla',   'en': 'Calculate Correlation Dim'},
        'chaos_calc_lyap':        {'tr': 'Lyapunov Hesapla',            'en': 'Calculate Lyapunov'},
        'chaos_poincare_group':   {'tr': 'Poincaré Kesiti',             'en': 'Poincaré Section'},
        'chaos_poincare_axis':    {'tr': 'Kesit Ekseni:',               'en': 'Section Axis:'},
        'chaos_poincare_value':   {'tr': 'Kesit Değeri:',               'en': 'Section Value:'},
        'chaos_poincare_dir':     {'tr': 'Geçiş Yönü:',                'en': 'Crossing Direction:'},
        'chaos_poincare_dir_up':  {'tr': 'Yukarı (+)',                  'en': 'Upward (+)'},
        'chaos_poincare_dir_down':{'tr': 'Aşağı (−)',                   'en': 'Downward (−)'},
        'chaos_poincare_dir_both':{'tr': 'Her İkisi',                   'en': 'Both'},
        'chaos_calc_poincare':    {'tr': 'Poincaré Kesitini Hesapla',   'en': 'Calculate Poincaré Section'},
        'plot_poincare':          {'tr': 'Poincaré Kesiti',             'en': 'Poincaré Section'},

        # Embedding panel
        'embed_title':         {'tr': 'Faz Uzayı Görselleştirme',  'en': 'Phase Space Visualization'},
        'embed_params':        {'tr': 'Parametreler',               'en': 'Parameters'},
        'embed_manual':        {'tr': 'Manuel Parametreleri Kullan','en': 'Use Manual Parameters'},
        'embed_visualization': {'tr': 'Görselleştirme',             'en': 'Visualization'},
        'embed_2d':            {'tr': '2D Faz Uzayı (x(t) vs x(t+τ))', 'en': '2D Phase Space (x(t) vs x(t+τ))'},
        'embed_3d':            {'tr': '3D Faz Uzayı (m=3)',         'en': '3D Phase Space (m=3)'},
        'embed_return':        {'tr': 'Geri Dönüş Haritası (x(t) vs x(t+1))', 'en': 'Return Map (x(t) vs x(t+1))'},
        'embed_multi':         {'tr': 'Çok-Boyutlu İzdüşüm',       'en': 'Multi-Dimensional Projection'},

        # Linear analysis panel
        'linear_analysis_lbl': {'tr': 'Analiz:',          'en': 'Analysis:'},
        'linear_max_lag':      {'tr': 'Maks. Gecikme:',   'en': 'Max Lag:'},
        'linear_window':       {'tr': 'Pencere:',          'en': 'Window:'},
        'linear_window_none':  {'tr': 'Yok',              'en': 'None'},

        # Parameter estimation panel
        'param_max_lag':       {'tr': 'Maks. Gecikme:',   'en': 'Max Lag:'},
        'param_max_dim':       {'tr': 'Maks. Boyut:',     'en': 'Max Dimension:'},

        # Results panel
        'results_title':       {'tr': '📊 Analiz Sonuçları Özeti', 'en': '📊 Analysis Results Summary'},
        'results_interp':      {'tr': 'Sistem Yorumu',    'en': 'System Interpretation'},
        'results_interp_wait': {'tr': 'Sistem yorumunu görmek için tüm analiz adımlarını tamamlayın.',
                                'en': 'Complete all analysis steps to see the system interpretation.'},
        'results_interp_chaos':{'tr': 'Sistem yorumunu görmek için kaos analizini tamamlayın.',
                                'en': 'Complete chaos analysis to see the system interpretation.'},
        'results_interp_lyap': {'tr': 'Sistem yorumunu görmek için Lyapunov üstelini hesaplayın.',
                                'en': 'Calculate the Lyapunov exponent to see the system interpretation.'},
        'results_yes':         {'tr': 'Evet',             'en': 'Yes'},
        'results_no':          {'tr': 'Hayır',            'en': 'No'},
        'results_detrend':     {'tr': 'Trend Giderme:',   'en': 'Detrending:'},
        'results_normalize':   {'tr': 'Normalizasyon:',   'en': 'Normalization:'},
        
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
        """Allow using TranslationManager as a callable for backward compatibility"""
        return self.get_text(key)
