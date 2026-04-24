"""
Content panel — orta panel, analiz adimina gore kontrolleri gosterir.
Veri yuklendiginde Excel benzeri tablo gosterilir.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QStackedWidget, QSplitter
)
from PySide6.QtCore import Qt, Signal
import numpy as np

from .data_load_panel import DataLoadPanel
from .data_table_panel import DataTablePanel
from .preprocessing_panel import PreprocessingPanel
from .linear_analysis_panel import LinearAnalysisPanel
from .parameter_estimation_panel import ParameterEstimationPanel
from .embedding_panel import EmbeddingPanel
from .chaos_analysis_panel import ChaosAnalysisPanel


class ContentPanel(QWidget):
    """Orta panel — kontrol panelleri + veri tablosu"""

    plot_requested = Signal(dict)

    def __init__(self, translation_manager, theme_manager):
        super().__init__()
        self.tm = translation_manager
        self.theme_manager = theme_manager
        self.current_data = None
        
        # Her adim icin son cizilen plot verisini sakla
        self.last_plot_data = {}  # {step_index: plot_data}
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Dikey splitter: ust kisim kontroller, alt kisim veri tablosu
        self.vsplitter = QSplitter(Qt.Vertical)

        # --- Ust: Stacked widget (kontroller) ---
        self.stacked_widget = QStackedWidget()

        # 0 — Data Loading
        self.data_load_panel = DataLoadPanel(self.tm)
        self.data_load_panel.data_loaded.connect(self.on_data_loaded)
        self.stacked_widget.addWidget(self.data_load_panel)

        # 1 — Preprocessing
        self.preprocessing_panel = PreprocessingPanel(self.tm)
        self.preprocessing_panel.plot_requested.connect(self._forward_plot)
        self.preprocessing_panel.data_preprocessed.connect(self.on_data_preprocessed)
        self.stacked_widget.addWidget(self.preprocessing_panel)

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

        # 4 — Phase Space (Embedding Visualization)
        self.embedding_panel = EmbeddingPanel(self.tm)
        self.embedding_panel.plot_requested.connect(self._forward_plot)
        self.stacked_widget.addWidget(self.embedding_panel)

        # 5 — Chaos Analysis
        self.chaos_panel = ChaosAnalysisPanel(self.tm)
        self.chaos_panel.analysis_complete.connect(self.on_chaos_analysis_complete)
        self.chaos_panel.plot_requested.connect(self._forward_plot)
        self.stacked_widget.addWidget(self.chaos_panel)

        # 6 — Results (placeholder)
        placeholder7 = QLabel("Step 7: Results Summary\n\nComing soon...")
        placeholder7.setAlignment(Qt.AlignCenter)
        self.stacked_widget.addWidget(placeholder7)

        self.vsplitter.addWidget(self.stacked_widget)

        # --- Alt: Data Tables (tum adimlar icin ortak) ---
        # İkinci bir horizontal splitter - iki tablo yan yana
        self.table_splitter = QSplitter(Qt.Horizontal)
        
        self.data_table_1 = DataTablePanel(self.tm)
        self.data_table_1.setMinimumHeight(200)
        self.table_splitter.addWidget(self.data_table_1)
        
        self.data_table_2 = DataTablePanel(self.tm)
        self.data_table_2.setMinimumHeight(200)
        self.data_table_2.setVisible(False)  # Başlangıçta gizli
        self.table_splitter.addWidget(self.data_table_2)
        
        # İki tablo eşit boyut
        self.table_splitter.setSizes([5000, 5000])
        
        self.vsplitter.addWidget(self.table_splitter)
        
        # Splitter oranlarini sonra set et (window resize sonrasi)
        # %30 kontroller, %70 tablo olacak sekilde
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.vsplitter.setSizes([3000, 7000]))

        # Splitter handle stilini ayarla (gorunur yap)
        self.vsplitter.setHandleWidth(6)
        self.vsplitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #555555;
                border: 1px solid #333333;
            }
            QSplitter::handle:hover {
                background-color: #777777;
            }
        """)

        layout.addWidget(self.vsplitter)

    def _forward_plot(self, plot_data: dict):
        """Forward plot request and update data table"""
        print(f"[TABLE] _forward_plot: type={plot_data.get('type')}")
        self.plot_requested.emit(plot_data)
        self._update_table_from_plot(plot_data)
        
        # Hangi adimdan geldigini tespit et ve sakla
        current_step = self.stacked_widget.currentIndex()
        
        # Step 3 (Parameter Estimation) icin ozel - iki plot sakla
        if current_step == 3:
            ptype = plot_data.get('type', '')
            if ptype == 'param_tau':
                # Tau plot'u - ilk tabloda goster ve sakla
                if not hasattr(self, 'param_tau_plot'):
                    self.param_tau_plot = {}
                self.param_tau_plot = plot_data
                print(f"[TABLE] Saved tau plot for step {current_step}")
            elif ptype == 'param_m':
                # M plot'u - ikinci tabloda goster ve sakla
                if not hasattr(self, 'param_m_plot'):
                    self.param_m_plot = {}
                self.param_m_plot = plot_data
                print(f"[TABLE] Saved m plot for step {current_step}")
                # İki plot da varsa cache'e kaydet
                if hasattr(self, 'param_tau_plot') and self.param_tau_plot:
                    self.last_plot_data[current_step] = {
                        'dual': True,
                        'plot1': self.param_tau_plot,
                        'plot2': self.param_m_plot
                    }
                else:
                    self.last_plot_data[current_step] = plot_data
        else:
            # Diger adimlar icin normal kaydet
            self.last_plot_data[current_step] = plot_data
            print(f"[TABLE] Saved plot_data for step {current_step}")
    
    def _update_table_from_plot(self, plot_data: dict):
        """Extract data from plot_data and display in table"""
        from core.timeseries import TimeSeries
        
        ptype = plot_data.get('type', '')
        print(f"[TABLE] _update_table_from_plot: type={ptype}")
        
        # Extract x, y arrays based on plot type
        x_data = None
        y_data = None
        dt = 1.0
        metadata = {}
        
        if ptype == 'timeseries':
            x_data = plot_data.get('time', np.array([]))
            y_data = plot_data.get('data', np.array([]))
            dt = x_data[1] - x_data[0] if len(x_data) > 1 else 1.0
            metadata = plot_data.get('metadata', {})
            if not metadata:
                metadata = {'system': 'Time Series'}
            
        elif ptype == 'linear':
            results = plot_data.get('results', {})
            atype = plot_data.get('analysis_type', 'acf')
            print(f"[TABLE] Linear: atype={atype}, keys={list(results.keys())}")
            if atype == 'acf':
                x_data = results.get('lags', np.array([]))
                y_data = results.get('acf', np.array([]))
                metadata = {'system': 'ACF', 'value_unit': 'correlation'}
                print(f"[TABLE] ACF data: lags={len(x_data)}, acf={len(y_data)}")
            elif atype == 'pacf':
                x_data = results.get('lags', np.array([]))
                y_data = results.get('pacf', np.array([]))
                metadata = {'system': 'PACF', 'value_unit': 'correlation'}
            elif atype == 'fft':
                x_data = results.get('frequencies', np.array([]))
                y_data = results.get('power', np.array([]))
                metadata = {'system': 'FFT Power Spectrum', 'value_unit': 'power'}
            dt = 1.0
            
        elif ptype == 'param_tau':
            results = plot_data.get('results', {})
            x_data = results.get('lags', np.array([]))
            y_data = results.get('ami', np.array([]))
            dt = 1.0
            metadata = {'system': 'AMI (Time Delay)', 'value_unit': 'bits'}
            
        elif ptype == 'param_m':
            results = plot_data.get('results', {})
            x_data = results.get('dimensions', np.array([]))  # 'dims' değil 'dimensions'
            y_data = results.get('fnn', np.array([]))  # 'fnn_pct' değil 'fnn'
            dt = 1.0
            metadata = {'system': 'FNN (Embedding Dim)', 'value_unit': '%'}
            print(f"[TABLE] FNN data: dimensions={len(x_data)}, fnn={len(y_data)}")
            
        elif ptype == 'chaos_lyapunov':
            results = plot_data.get('results', {})
            if 't_steps' in results and 'divergence' in results:
                x_data = results.get('t_steps', np.array([]))
                y_data = results.get('divergence', np.array([]))
                dt = x_data[1] - x_data[0] if len(x_data) > 1 else 1.0
                metadata = {'system': 'Lyapunov Divergence'}
            else:
                # Single point
                x_data = np.array([0])
                y_data = np.array([results.get('lyapunov', 0)])
                dt = 1.0
                metadata = {'system': 'Lyapunov Exponent'}
        
        elif ptype == 'chaos_spectrum':
            exponents = plot_data.get('exponents', np.array([]))
            x_data = np.arange(len(exponents))
            y_data = exponents
            dt = 1.0
            metadata = {'system': 'Lyapunov Spectrum', 'value_unit': 'nats/s'}
        
        elif ptype == 'chaos_correlation':
            results = plot_data.get('results', {})
            radii = results.get('radii', np.array([]))
            c_r = results.get('c_r', np.array([]))
            valid = c_r > 0
            if np.any(valid):
                x_data = np.log(radii[valid])
                y_data = np.log(c_r[valid])
            else:
                x_data = np.array([])
                y_data = np.array([])
            dt = 1.0
            metadata = {'system': 'Correlation Dimension', 'value_unit': 'log(C(r))'}
        
        elif ptype == 'preprocessing':
            x_data = plot_data.get('time_processed', np.array([]))
            y_data = plot_data.get('data_processed', np.array([]))
            dt = x_data[1] - x_data[0] if len(x_data) > 1 else 1.0
            op = plot_data.get('operation', 'Unknown')
            metadata = {'system': f'Preprocessing: {op}'}
        
        elif ptype == 'embedding_2d':
            embedded = plot_data.get('embedded', np.array([]))
            if embedded.ndim == 2 and embedded.shape[1] >= 2:
                x_data = embedded[:, 0]
                y_data = embedded[:, 1]
            else:
                x_data = np.array([])
                y_data = np.array([])
            dt = 1.0
            metadata = {'system': '2D Phase Space'}
        
        elif ptype == 'return_map':
            x_data = plot_data.get('x', np.array([]))
            y_data = plot_data.get('y', np.array([]))
            dt = 1.0
            metadata = {'system': 'Return Map'}
        
        else:
            # Unknown type, don't update table
            return
        
        # Create TimeSeries and display
        if x_data is not None and y_data is not None and len(x_data) > 0:
            print(f"[TABLE] Creating table: x={len(x_data)}, y={len(y_data)}, meta={metadata.get('system', 'N/A')}")
            # Use y_data as the main data, x_data becomes time axis
            ts = TimeSeries(data=y_data, dt=dt, metadata=metadata)
            # Override time with x_data
            ts.time = x_data
            
            # Hangi tabloya yazilacagini belirle
            if ptype == 'param_tau':
                # Tau → Table 1
                self.data_table_2.setVisible(True)  # İkinci tabloyu goster
                self.data_table_1.set_data(ts)
                print("[TABLE] Table 1 (tau) updated!")
            elif ptype == 'param_m':
                # M → Table 2
                self.data_table_2.setVisible(True)  # İkinci tabloyu goster
                self.data_table_2.set_data(ts)
                print("[TABLE] Table 2 (m) updated!")
            else:
                # Diger tipler → Table 1, Table 2'yi gizle
                self.data_table_2.setVisible(False)
                self.data_table_1.set_data(ts)
                print("[TABLE] Table 1 updated!")
        else:
            print(f"[TABLE] SKIP: x={x_data is not None}, y={y_data is not None}, len={len(x_data) if x_data is not None else 0}")

    def on_data_loaded(self, timeseries):
        self.current_data = timeseries

        # Tabloyu guncelle
        self.data_table_1.set_data(timeseries)

        # Grafik panele zaman serisi gonder
        plot_data = {
            'type': 'timeseries',
            'time': timeseries.time,
            'data': timeseries.data,
            'metadata': timeseries.metadata
        }
        self.plot_requested.emit(plot_data)
        
        # Step 0 icin plot data'yi sakla
        self.last_plot_data[0] = plot_data

        # Adimlari ac ve ilk adimi tamamlanmis olarak isaretle
        main_window = self.window()
        if hasattr(main_window, 'steps_panel'):
            main_window.steps_panel.mark_step_completed(0)  # Data load completed
            main_window.steps_panel.unlock_step(1)
            main_window.steps_panel.unlock_step(2)

        self.linear_analysis_panel.set_data(timeseries)
        self.parameter_panel.set_data(timeseries)
        self.preprocessing_panel.set_data(timeseries)

    def on_linear_analysis_complete(self, results):
        main_window = self.window()
        if hasattr(main_window, 'steps_panel'):
            main_window.steps_panel.mark_step_completed(2)  # Linear analysis completed
            main_window.steps_panel.unlock_step(3)

    def on_parameters_estimated(self, params):
        if 'tau' in params and 'm' in params:
            tau = params['tau']
            m = params['m']
            main_window = self.window()
            if hasattr(main_window, 'steps_panel'):
                main_window.steps_panel.mark_step_completed(3)  # Parameter estimation completed
                main_window.steps_panel.unlock_step(4)
                main_window.steps_panel.unlock_step(5)
            
            # Embedding panel'e parametreleri gönder
            self.embedding_panel.set_data(self.current_data, tau, m)
            
            # Chaos panel'e parametreleri gönder
            self.chaos_panel.set_data(self.current_data, tau, m)

    def on_chaos_analysis_complete(self, results):
        main_window = self.window()
        if hasattr(main_window, 'steps_panel'):
            main_window.steps_panel.mark_step_completed(5)  # Chaos analysis completed
            main_window.steps_panel.unlock_step(6)

    def on_data_preprocessed(self, timeseries):
        """On isleme sonrasi guncellenmis veriyi diger panellere ilet"""
        self.current_data = timeseries
        self.data_table_1.set_data(timeseries)
        
        # Preprocessing sonrasi analiz sonuclarini sifirla (cunku veri degisti)
        # Step 2-6 icin kaydedilmis plot'lari temizle
        for step in [2, 3, 4, 5, 6]:
            if step in self.last_plot_data:
                del self.last_plot_data[step]
        
        # Parameter estimation cache'lerini de temizle
        if hasattr(self, 'param_tau_plot'):
            self.param_tau_plot = None
        if hasattr(self, 'param_m_plot'):
            self.param_m_plot = None
        
        # Mark preprocessing as completed
        main_window = self.window()
        if hasattr(main_window, 'steps_panel'):
            main_window.steps_panel.mark_step_completed(1)  # Preprocessing completed
        self.linear_analysis_panel.set_data(timeseries)
        self.parameter_panel.set_data(timeseries)
        self.chaos_panel.reset_data(timeseries)

        main_window = self.window()
        if hasattr(main_window, 'steps_panel'):
            main_window.steps_panel.lock_step(4)
            main_window.steps_panel.lock_step(5)
            main_window.steps_panel.lock_step(6)

    def reset_all(self):
        """Tüm panelleri sıfırla (yeni analiz için)"""
        self.current_data = None
        self.data_table_1.clear_table()
        self.data_table_2.clear_table()
        self.last_plot_data.clear()  # Tum kaydedilmis plot'lari sil
        self.stacked_widget.setCurrentIndex(0)  # Data Load paneline dön
        
        # Her paneli sıfırla
        if hasattr(self, 'parameter_panel'):
            self.parameter_panel.tau = None
            self.parameter_panel.m = None
            self.parameter_panel.tau_result_label.setText("τ = ?")
            self.parameter_panel.m_result_label.setText("m = ?")
        
        if hasattr(self, 'chaos_panel'):
            self.chaos_panel.tau = None
            self.chaos_panel.m = None

    def set_step(self, step_index):
        """Adim degistiginde tabloyu guncelle"""
        print(f"[TABLE] set_step({step_index}), cache keys={list(self.last_plot_data.keys())}")
        self.stacked_widget.setCurrentIndex(step_index)
        
        # Eger bu adim icin daha once plot cizilmisse onu goster
        if step_index in self.last_plot_data:
            cached_data = self.last_plot_data[step_index]
            print(f"[TABLE] Restoring cached plot for step {step_index}")
            
            # Step 3 dual-table mode mu kontrol et
            if isinstance(cached_data, dict) and cached_data.get('dual'):
                print("[TABLE] Dual-table mode - restoring both tables")
                self.data_table_2.setVisible(True)
                self._update_table_from_plot(cached_data['plot1'])  # Tau
                self._update_table_from_plot(cached_data['plot2'])  # M
            else:
                # Tek tablo mode
                self.data_table_2.setVisible(False)
                self._update_table_from_plot(cached_data)
        # Yoksa ham veriyi goster
        elif self.current_data is not None:
            print(f"[TABLE] No cache for step {step_index}, showing raw data")
            self.data_table_2.setVisible(False)
            self.data_table_1.set_data(self.current_data)

    def update_plot_theme(self):
        pass

    def refresh_ui(self):
        self.data_load_panel.refresh_ui()
        self.preprocessing_panel.refresh_ui()
        self.linear_analysis_panel.refresh_ui()
        self.parameter_panel.refresh_ui()
        self.chaos_panel.refresh_ui()
        self.data_table_1.refresh_ui()
        self.data_table_2.refresh_ui()
