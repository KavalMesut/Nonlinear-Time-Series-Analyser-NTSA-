"""
Data table panel — Excel benzeri tablo ile veriyi gosterir.
Sutun basliklari ve birimleri ile.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt
import numpy as np


class DataTablePanel(QWidget):
    """Excel benzeri veri tablosu paneli"""

    def __init__(self, translation_manager=None):
        super().__init__()
        self.tm = translation_manager if translation_manager is not None else (lambda k: k)
        self._current_timeseries = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Ozet bilgi grubu — referansları sakla ki refresh_ui güncelleyebilsin
        self._info_group = QGroupBox(self.tm("table_summary"))
        self._info_layout = QFormLayout()

        self.lbl_length = QLabel("-")
        self.lbl_dt = QLabel("-")
        self.lbl_duration = QLabel("-")
        self.lbl_system = QLabel("-")
        self.lbl_stats = QLabel("-")

        self._info_layout.addRow(self.tm("table_length") + ":", self.lbl_length)
        self._info_layout.addRow("dt:", self.lbl_dt)
        self._info_layout.addRow(self.tm("table_duration") + ":", self.lbl_duration)
        self._info_layout.addRow(self.tm("table_system") + ":", self.lbl_system)
        self._info_layout.addRow(self.tm("table_stats") + ":", self.lbl_stats)

        self._info_group.setLayout(self._info_layout)
        layout.addWidget(self._info_group)

        # Tablo
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # salt okunur
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        # Sutun genislikleri otomatik
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)

        layout.addWidget(self.table)

    def clear_table(self):
        """Tabloyu temizle"""
        self._current_timeseries = None
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.lbl_length.setText("-")
        self.lbl_dt.setText("-")
        self.lbl_duration.setText("-")
        self.lbl_system.setText("-")
        self.lbl_stats.setText("-")

    def set_data(self, timeseries):
        """TimeSeries verisini tabloya yukle"""
        self._current_timeseries = timeseries
        data = timeseries.data
        time = timeseries.time
        dt = timeseries.dt
        meta = timeseries.metadata or {}
        n = len(data)

        # Ozet bilgi guncelle
        pts_label = self.tm('data_n_points') if self.tm('data_n_points') != 'data_n_points' else 'points'
        self.lbl_length.setText(f"{n:,} {pts_label}")
        self.lbl_dt.setText(f"{dt}")
        self.lbl_duration.setText(f"{n * dt:.2f}")
        unknown_label = self.tm('msg_unknown') if self.tm('msg_unknown') != 'msg_unknown' else '?'
        system_name = self._localize_system_name(meta.get('system', unknown_label))
        self.lbl_system.setText(system_name)
        mean_lbl = 'Ort' if self.tm('table_mean') == 'table_mean' else self.tm('table_mean')
        std_lbl  = 'Std' if self.tm('table_std')  == 'table_std'  else self.tm('table_std')
        self.lbl_stats.setText(
            f"Min={np.min(data):.4f}  Max={np.max(data):.4f}  "
            f"{mean_lbl}={np.mean(data):.4f}  {std_lbl}={np.std(data):.4f}"
        )

        # Birim tahmini
        time_unit = self._guess_time_unit(dt, meta)
        value_unit = self._guess_value_unit(meta)

        # Çok değişkenli ODE: all_vars_data metadata'da var mı?
        all_vars = meta.get('all_vars_data', {})
        var_names_list = list(all_vars.keys()) if all_vars and len(all_vars) > 1 else []
        is_multi = bool(var_names_list)

        time_word  = self.tm("table_time")  if self.tm("table_time")  != "table_time"  else "Time"
        value_word = self.tm("table_value") if self.tm("table_value") != "table_value" else "Value"
        if is_multi:
            self.table.setColumnCount(2 + len(var_names_list))
            headers = ([self.tm("table_index"),
                        f"{time_word} ({time_unit})" if time_unit else time_word]
                       + var_names_list)
        else:
            self.table.setColumnCount(3)
            headers = [
                self.tm("table_index"),
                f"{time_word} ({time_unit})" if time_unit else time_word,
                f"{value_word} ({value_unit})" if value_unit else value_word,
            ]
        self.table.setHorizontalHeaderLabels(headers)

        # Performans: en fazla 100_000 satir goster
        display_n = min(n, 100_000)
        self.table.setRowCount(display_n)

        var_arrays = [all_vars[vn] for vn in var_names_list] if is_multi else [data]

        for i in range(display_n):
            col = 0
            idx_item = QTableWidgetItem(str(i))
            idx_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, col, idx_item); col += 1

            t_item = QTableWidgetItem(f"{time[i]:.6g}")
            t_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, col, t_item); col += 1

            for arr in var_arrays:
                v_item = QTableWidgetItem(f"{arr[i]:.6g}")
                v_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(i, col, v_item); col += 1

        # Sutun genisliklerini ayarla
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

        if n > display_n:
            pts_label = self.tm('data_n_points') if self.tm('data_n_points') != 'data_n_points' else 'points'
            self.lbl_length.setText(f"{n:,} {pts_label} (ilk {display_n:,})")

    def _guess_time_unit(self, dt, meta):
        """dt ve meta bilgisinden zaman birimini tahmin et"""
        if 'time_unit' in meta:
            return meta['time_unit']

        system = meta.get('system', '').lower()

        # Ayrik haritalar (dt=1) → adim (n)
        if dt == 1.0 and system in ('logistic', 'henon', 'tent', 'sine', 'ikeda'):
            return 'n'

        # Surekli sistemler
        if dt <= 0.01:
            return 's'
        elif dt <= 1.0:
            return 's'

        return ''

    def _guess_value_unit(self, meta):
        """Meta bilgisinden deger birimini tahmin et"""
        if 'value_unit' in meta:
            return meta['value_unit']

        system = meta.get('system', '').lower()

        unit_map = {
            'lorenz': 'x',
            'rossler': 'x',
            'chua': 'V',
            'chen': 'x',
            'duffing': 'x',
            'double_pendulum': 'rad',
            'logistic': 'x_n',
            'henon': 'x_n',
            'tent': 'x_n',
            'sine': 'x_n',
            'ikeda': 'x_n',
        }

        return unit_map.get(system, '')

    def _localize_system_name(self, system_name: str) -> str:
        """Sık görünen sistem/adım adlarını mevcut dile göre yerelleştir."""
        mapping = {
            'Time Series': self.tm('plot_time_series'),
            'ACF': 'ACF',
            'PACF': 'PACF',
            'FFT Power Spectrum': self.tm('plot_fft_power'),
            'AMI (Time Delay)': self.tm('plot_ami_delay'),
            'FNN (Embedding Dim)': self.tm('plot_fnn_dim'),
            'Lyapunov Divergence': self.tm('plot_lyapunov') + ' - sapma',
            'Lyapunov Exponent': self.tm('plot_lyapunov'),
            'Lyapunov Spectrum': self.tm('plot_lyapunov_spectrum'),
            'Correlation Dimension': self.tm('plot_correlation_dim'),
            '2D Phase Space': '2D Faz Uzayı',
            'Return Map': 'Geri Dönüş Haritası',
        }
        if isinstance(system_name, str) and system_name.startswith('Preprocessing: '):
            return f"{self.tm('plot_preprocessing')}: {system_name.split(': ', 1)[1]}"
        return mapping.get(system_name, system_name)

    def refresh_ui(self):
        """Dil değiştiğinde özet alanını ve mevcut tabloyu güncelle."""
        self._info_group.setTitle(self.tm("table_summary"))
        lbl = self._info_layout.labelForField(self.lbl_length)
        if lbl:
            lbl.setText(self.tm("table_length") + ":")
        lbl = self._info_layout.labelForField(self.lbl_dt)
        if lbl:
            lbl.setText(self.tm("data_timestep") + ":")
        lbl = self._info_layout.labelForField(self.lbl_duration)
        if lbl:
            lbl.setText(self.tm("table_duration") + ":")
        lbl = self._info_layout.labelForField(self.lbl_system)
        if lbl:
            lbl.setText(self.tm("table_system") + ":")
        lbl = self._info_layout.labelForField(self.lbl_stats)
        if lbl:
            lbl.setText(self.tm("table_stats") + ":")
        if self._current_timeseries is not None:
            self.set_data(self._current_timeseries)
