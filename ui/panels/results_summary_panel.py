"""
Results Summary Panel - All analysis results overview
Shows summary cards for all completed analysis steps.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QLabel, QGridLayout
)
from PySide6.QtCore import Qt


class ResultsSummaryPanel(QWidget):
    """
    Results summary panel showing all analysis results.
    """
    
    def __init__(self, translation_manager, theme_manager=None):
        super().__init__()
        self.tm = translation_manager
        self.theme_manager = theme_manager
        self.results_data = {}
        self.init_ui()
    
    def init_ui(self):
        # Main layout - no scroll
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 10)
        layout.setSpacing(10)
        
        # Title - left aligned
        title = QLabel(self.tm("results_title"))
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #268bd2;")
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)
        
        # Results cards grid - 2 rows x 3 columns for better spacing
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(15)
        self.cards_layout.setColumnStretch(0, 1)
        self.cards_layout.setColumnStretch(1, 1)
        self.cards_layout.setColumnStretch(2, 1)
        self.cards_layout.setColumnStretch(1, 1)
        self.cards_layout.setColumnStretch(2, 1)
        
        # 1. Data Info Card
        self.data_card = self._create_card("1. Veri Bilgileri", [
            ("Dosya:", "—"),
            ("Örnekleme (dt):", "—"),
            ("Nokta (N):", "—"),
            ("Süre:", "—")
        ])
        self.cards_layout.addWidget(self.data_card, 0, 0)
        
        # 2. Preprocessing Card
        self.preproc_card = self._create_card("2. Ön İşleme", [
            (self.tm("results_detrend"), "—"),
            (self.tm("results_normalize"), "—"),
            ("Yumuşatma:", "—")
        ])
        self.cards_layout.addWidget(self.preproc_card, 0, 1)
        
        # 3. Linear Analysis Card
        self.linear_card = self._create_card("3. Doğrusal Analiz", [
            ("ACF Azalması:", "—"),
            ("PACF Gecikme:", "—"),
            ("FFT Pik (Hz):", "—")
        ])
        self.cards_layout.addWidget(self.linear_card, 0, 2)
        
        # 4. Parameter Estimation Card
        self.param_card = self._create_card("4. Parametre Tahmini", [
            ("τ (AMI):", "—"),
            ("m (FNN):", "—")
        ])
        self.cards_layout.addWidget(self.param_card, 1, 0)
        
        # 5. Phase Space Card
        self.phase_card = self._create_card("5. Faz Uzayı", [
            ("Kullanılan τ:", "—"),
            ("Kullanılan m:", "—"),
            ("Boyut:", "—")
        ])
        self.cards_layout.addWidget(self.phase_card, 1, 1)
        
        # 6. Chaos Analysis Card
        self.chaos_card = self._create_card("6. Kaos Analizi", [
            ("Lyapunov (λ₁):", "—"),
            ("Spektrum:", "—"),
            ("Korelasyon (D₂):", "—"),
            ("Kaplan-Yorke:", "—")
        ])
        self.cards_layout.addWidget(self.chaos_card, 1, 2)
        
        layout.addLayout(self.cards_layout)
        
        # Interpretation section
        interp_group = QGroupBox(self.tm("results_interp"))
        interp_layout = QVBoxLayout()
        
        self.interp_label = QLabel(self.tm("results_interp_wait"))
        self.interp_label.setWordWrap(True)
        self.interp_label.setStyleSheet("font-size: 12pt; padding: 10px;")
        interp_layout.addWidget(self.interp_label)
        
        interp_group.setLayout(interp_layout)
        layout.addWidget(interp_group)
        
        layout.addStretch()
    
    def _create_card(self, title, fields):
        """Create a summary card with title and field rows."""
        card = QGroupBox(title)
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #268bd2;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        # Store labels for later updates
        card.field_labels = {}
        
        for field_name, default_value in fields:
            row = QHBoxLayout()
            name_label = QLabel(field_name)
            name_label.setStyleSheet("font-weight: normal;")
            value_label = QLabel(default_value)
            value_label.setStyleSheet("font-weight: bold; color: #268bd2;")
            
            row.addWidget(name_label)
            row.addStretch()
            row.addWidget(value_label)
            
            layout.addLayout(row)
            card.field_labels[field_name] = value_label
        
        card.setLayout(layout)
        return card
    
    def update_data_info(self, filename, dt, n_points, duration):
        """Update data information card."""
        self.data_card.field_labels["Dosya:"].setText(filename)
        self.data_card.field_labels["Örnekleme (dt):"].setText(f"{dt:.4f}")
        self.data_card.field_labels["Nokta (N):"].setText(str(n_points))
        self.data_card.field_labels["Süre:"].setText(f"{duration:.2f} s")
        
        self.results_data['data'] = {
            'filename': filename,
            'dt': dt,
            'n_points': n_points,
            'duration': duration
        }
        self._update_interpretation()
    
    def update_preprocessing(self, detrend, normalize, smoothing):
        """Update preprocessing card."""
        self.preproc_card.field_labels[self.tm("results_detrend")].setText(self.tm("results_yes") if detrend else self.tm("results_no"))
        self.preproc_card.field_labels[self.tm("results_normalize")].setText(self.tm("results_yes") if normalize else self.tm("results_no"))
        self.preproc_card.field_labels["Yumuşatma:"].setText(smoothing if smoothing else "Yok")
        
        self.results_data['preprocessing'] = {
            'detrend': detrend,
            'normalize': normalize,
            'smoothing': smoothing
        }
        self._update_interpretation()
    
    def update_linear_analysis(self, acf_decay=None, pacf_lags=None, fft_peak=None):
        """Update linear analysis card."""
        if acf_decay is not None:
            self.linear_card.field_labels["ACF Azalması:"].setText(f"{acf_decay:.3f}")
        if pacf_lags is not None:
            self.linear_card.field_labels["PACF Gecikme:"].setText(str(pacf_lags))
        if fft_peak is not None:
            self.linear_card.field_labels["FFT Pik (Hz):"].setText(f"{fft_peak:.4f}")
        
        self.results_data['linear'] = {
            'acf_decay': acf_decay,
            'pacf_lags': pacf_lags,
            'fft_peak': fft_peak
        }
        self._update_interpretation()
    
    def update_parameters(self, tau=None, m=None):
        """Update parameter estimation card."""
        if tau is not None:
            self.param_card.field_labels["τ (AMI):"].setText(str(tau))
            self.results_data.setdefault('parameters', {})['tau'] = tau
        if m is not None:
            self.param_card.field_labels["m (FNN):"].setText(str(m))
            self.results_data.setdefault('parameters', {})['m'] = m
        
        self._update_interpretation()
    
    def update_phase_space(self, tau, m):
        """Update phase space card."""
        self.phase_card.field_labels["Kullanılan τ:"].setText(str(tau))
        self.phase_card.field_labels["Kullanılan m:"].setText(str(m))
        self.phase_card.field_labels["Boyut:"].setText(f"{m}D")
        
        self.results_data['phase_space'] = {'tau': tau, 'm': m}
        self._update_interpretation()
    
    def update_chaos_analysis(self, lyapunov=None, spectrum=None, corr_dim=None, ky_dim=None):
        """Update chaos analysis card."""
        if lyapunov is not None:
            self.chaos_card.field_labels["Lyapunov (λ₁):"].setText(f"{lyapunov:.6f}")
            self.results_data.setdefault('chaos', {})['lyapunov'] = lyapunov
        
        if spectrum is not None:
            spec_str = ", ".join([f"{s:.4f}" for s in spectrum[:3]])  # First 3 exponents
            if len(spectrum) > 3:
                spec_str += "..."
            self.chaos_card.field_labels["Spektrum:"].setText(spec_str)
            self.results_data.setdefault('chaos', {})['spectrum'] = spectrum
        
        if corr_dim is not None:
            self.chaos_card.field_labels["Korelasyon (D₂):"].setText(f"{corr_dim:.4f}")
            self.results_data.setdefault('chaos', {})['corr_dim'] = corr_dim
        
        if ky_dim is not None:
            self.chaos_card.field_labels["Kaplan-Yorke:"].setText(f"{ky_dim:.4f}")
            self.results_data.setdefault('chaos', {})['ky_dim'] = ky_dim
        
        self._update_interpretation()
    
    def _update_interpretation(self):
        """Update system interpretation based on all results."""
        if 'chaos' not in self.results_data:
            self.interp_label.setText(self.tm("results_interp_chaos"))
            return
        
        chaos = self.results_data.get('chaos', {})
        lyap = chaos.get('lyapunov')
        corr_dim = chaos.get('corr_dim')
        
        if lyap is None:
            self.interp_label.setText(self.tm("results_interp_lyap"))
            return
        
        # Interpretation logic
        interp_text = "<b>Sistem Analizi:</b><br><br>"
        
        # Lyapunov interpretation
        if lyap > 0.001:
            interp_text += "✅ <b>Kaotik Davranış Tespit Edildi</b><br>"
            interp_text += f"   • Pozitif Lyapunov üsteli (λ₁ = {lyap:.6f})<br>"
            interp_text += "   • Sistem başlangıç koşullarına duyarlılık gösteriyor<br>"
            interp_text += "   • Yakın yörüngeler üstel olarak ıraksar<br><br>"
        elif lyap > -0.001:
            interp_text += "⚠️ <b>Marjinal/Quasi-Periyodik Davranış</b><br>"
            interp_text += f"   • Sıfıra yakın Lyapunov üsteli (λ₁ = {lyap:.6f})<br>"
            interp_text += "   • Sistem periyodik veya quasi-periyodik olabilir<br><br>"
        else:
            interp_text += "❌ <b>Kaotik Olmayan (Kararlı) Sistem</b><br>"
            interp_text += f"   • Negatif Lyapunov üsteli (λ₁ = {lyap:.6f})<br>"
            interp_text += "   • Yörüngeler yakınsar (kararlı sabit nokta/limit çevrimi)<br><br>"
        
        # Correlation dimension interpretation
        if corr_dim is not None:
            interp_text += f"<b>Çekici Boyutu:</b> D₂ = {corr_dim:.4f}<br>"
            if corr_dim < 3:
                interp_text += "   • Düşük boyutlu çekici<br>"
            else:
                interp_text += "   • Yüksek boyutlu dinamikler<br>"
        
        self.interp_label.setText(interp_text)
    
    def clear(self):
        """Clear all results."""
        self.results_data = {}
        
        # Reset all cards to default
        for card in [self.data_card, self.preproc_card, self.linear_card, 
                     self.param_card, self.phase_card, self.chaos_card]:
            for label in card.field_labels.values():
                label.setText("—")
        
        self.interp_label.setText(self.tm("results_interp_wait"))
