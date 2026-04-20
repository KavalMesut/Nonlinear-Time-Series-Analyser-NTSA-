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
        self.tm = translation_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Ozet bilgi grubu
        info_group = QGroupBox("Veri Ozeti")
        info_layout = QFormLayout()

        self.lbl_length = QLabel("-")
        self.lbl_dt = QLabel("-")
        self.lbl_duration = QLabel("-")
        self.lbl_system = QLabel("-")
        self.lbl_stats = QLabel("-")

        info_layout.addRow("Uzunluk:", self.lbl_length)
        info_layout.addRow("dt:", self.lbl_dt)
        info_layout.addRow("Toplam Sure:", self.lbl_duration)
        info_layout.addRow("Sistem:", self.lbl_system)
        info_layout.addRow("Istatistik:", self.lbl_stats)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

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

    def set_data(self, timeseries):
        """TimeSeries verisini tabloya yukle"""
        data = timeseries.data
        time = timeseries.time
        dt = timeseries.dt
        meta = timeseries.metadata or {}
        n = len(data)

        # Ozet bilgi guncelle
        self.lbl_length.setText(f"{n:,} nokta")
        self.lbl_dt.setText(f"{dt}")
        self.lbl_duration.setText(f"{n * dt:.2f}")
        system_name = meta.get('system', 'Bilinmiyor')
        self.lbl_system.setText(system_name)
        self.lbl_stats.setText(
            f"Min={np.min(data):.4f}  Max={np.max(data):.4f}  "
            f"Ort={np.mean(data):.4f}  Std={np.std(data):.4f}"
        )

        # Birim tahmini
        time_unit = self._guess_time_unit(dt, meta)
        value_unit = self._guess_value_unit(meta)

        # Sutunlar: Index, Time, Value
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            "Index",
            f"Zaman ({time_unit})" if time_unit else "Zaman",
            f"Deger ({value_unit})" if value_unit else "Deger"
        ])

        # Performans: en fazla 100_000 satir goster
        display_n = min(n, 100_000)
        self.table.setRowCount(display_n)

        for i in range(display_n):
            # Index
            idx_item = QTableWidgetItem(str(i))
            idx_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 0, idx_item)

            # Time
            t_item = QTableWidgetItem(f"{time[i]:.6g}")
            t_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 1, t_item)

            # Value
            v_item = QTableWidgetItem(f"{data[i]:.6g}")
            v_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 2, v_item)

        # Sutun genisliklerini ayarla
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

        if n > display_n:
            self.lbl_length.setText(f"{n:,} nokta (ilk {display_n:,} gosteriliyor)")

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

    def refresh_ui(self):
        pass
